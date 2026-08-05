use std::fmt;
use std::fs::{self, File};
use std::io::Read;
use std::path::Path;


pub const MAX_RECORD_BYTES: usize = 512 * 1024;


#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ProjectRecord {
    Status,
    Manifest,
    WorkflowMap,
    UiMap,
    SimulationWorld,
    ProductBaselineHandoff,
}

impl ProjectRecord {
    fn relative_path(self) -> &'static str {
        match self {
            Self::Status => ".lccoding/status.json",
            Self::Manifest => ".lccoding/CANONICAL-MANIFEST.json",
            Self::WorkflowMap => ".lccoding/WORKFLOW-MAP.md",
            Self::UiMap => ".lccoding/UI-MAP.md",
            Self::SimulationWorld => ".lccoding/SIMULATION-WORLD.md",
            Self::ProductBaselineHandoff => ".lccoding/PRODUCT-BASELINE-HANDOFF.md",
        }
    }

    fn optional(self) -> bool {
        matches!(self, Self::Manifest)
    }
}


#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum InputError {
    RootInvalid,
    RecordInvalid,
    ReadRace,
    ResourceLimit,
}

impl InputError {
    pub const fn code(self) -> &'static str {
        match self {
            Self::RootInvalid => "BI_ROOT_INVALID",
            Self::RecordInvalid => "BI_RECORD_INVALID",
            Self::ReadRace => "BI_READ_RACE",
            Self::ResourceLimit => "BI_RESOURCE_LIMIT",
        }
    }
}

impl fmt::Display for InputError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.code())
    }
}

impl std::error::Error for InputError {}


pub fn validate_project_root(root: &Path) -> Result<(), InputError> {
    validate_directory_path(root, InputError::RootInvalid)?;
    validate_directory_path(&root.join(".lccoding"), InputError::RootInvalid)
}


pub(crate) fn validate_directory_path(path: &Path, error: InputError) -> Result<(), InputError> {
    platform::validate_directory(path, error)
}


pub(crate) fn read_control_file(
    anchor: &Path,
    parent: &Path,
    path: &Path,
    limit: usize,
) -> Result<Vec<u8>, InputError> {
    platform::read_stable_file(anchor, parent, path, limit)
}


pub fn read_project_record(
    root: &Path,
    record: ProjectRecord,
) -> Result<Option<String>, InputError> {
    validate_project_root(root)?;
    let path = root.join(record.relative_path());
    match fs::symlink_metadata(&path) {
        Ok(_) => {}
        Err(error) if error.kind() == std::io::ErrorKind::NotFound && record.optional() => {
            return Ok(None);
        }
        Err(_) => return Err(InputError::RecordInvalid),
    }

    let bytes = platform::read_stable_file(
        root,
        &root.join(".lccoding"),
        &path,
        MAX_RECORD_BYTES,
    )?;
    String::from_utf8(bytes)
        .map(Some)
        .map_err(|_| InputError::RecordInvalid)
}


#[cfg(windows)]
mod platform {
    use super::{File, InputError, Path, Read};
    use std::mem::MaybeUninit;
    use std::os::windows::ffi::OsStrExt;
    use std::os::windows::io::{AsRawHandle, FromRawHandle, RawHandle};

    use windows::Win32::Foundation::{GENERIC_READ, HANDLE};
    use windows::Win32::Storage::FileSystem::{
        BY_HANDLE_FILE_INFORMATION, CreateFileW, FILE_ATTRIBUTE_DIRECTORY,
        FILE_ATTRIBUTE_REPARSE_POINT, FILE_FLAG_BACKUP_SEMANTICS,
        FILE_FLAG_OPEN_REPARSE_POINT, FILE_SHARE_DELETE, FILE_SHARE_READ,
        FILE_SHARE_WRITE, GetFileInformationByHandle, OPEN_EXISTING,
    };
    use windows::core::PCWSTR;

    #[derive(Clone, Copy, Debug, Eq, PartialEq)]
    struct Identity {
        volume: u32,
        index: u64,
        size: u64,
        attributes: u32,
    }

    fn wide(path: &Path) -> Vec<u16> {
        path.as_os_str().encode_wide().chain(Some(0)).collect()
    }

    fn information(file: &File) -> Result<Identity, InputError> {
        let mut raw = MaybeUninit::<BY_HANDLE_FILE_INFORMATION>::zeroed();
        unsafe {
            GetFileInformationByHandle(HANDLE(file.as_raw_handle()), raw.as_mut_ptr())
                .map_err(|_| InputError::RecordInvalid)?;
            let value = raw.assume_init();
            Ok(Identity {
                volume: value.dwVolumeSerialNumber,
                index: ((value.nFileIndexHigh as u64) << 32) | value.nFileIndexLow as u64,
                size: ((value.nFileSizeHigh as u64) << 32) | value.nFileSizeLow as u64,
                attributes: value.dwFileAttributes,
            })
        }
    }

    fn open(path: &Path, directory: bool) -> Result<(File, Identity), InputError> {
        let path = wide(path);
        let flags = FILE_FLAG_OPEN_REPARSE_POINT
            | if directory {
                FILE_FLAG_BACKUP_SEMANTICS
            } else {
                Default::default()
            };
        let handle = unsafe {
            CreateFileW(
                PCWSTR(path.as_ptr()),
                if directory { 0 } else { GENERIC_READ.0 },
                FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                None,
                OPEN_EXISTING,
                flags,
                None,
            )
            .map_err(|_| InputError::RecordInvalid)?
        };
        let file = unsafe { File::from_raw_handle(handle.0 as RawHandle) };
        let identity = information(&file)?;
        if identity.attributes & FILE_ATTRIBUTE_REPARSE_POINT.0 != 0 {
            return Err(InputError::RecordInvalid);
        }
        let is_directory = identity.attributes & FILE_ATTRIBUTE_DIRECTORY.0 != 0;
        if is_directory != directory {
            return Err(InputError::RecordInvalid);
        }
        Ok((file, identity))
    }

    pub fn validate_directory(path: &Path, error: InputError) -> Result<(), InputError> {
        open(path, true).map(|_| ()).map_err(|_| error)
    }

    pub fn read_stable_file(
        root: &Path,
        parent: &Path,
        path: &Path,
        limit: usize,
    ) -> Result<Vec<u8>, InputError> {
        let (_, root_before) = open(root, true).map_err(|_| InputError::RootInvalid)?;
        let (_, directory_before) = open(parent, true).map_err(|_| InputError::RootInvalid)?;
        let (mut file, file_before) = open(path, false)?;

        if file_before.size > limit as u64 {
            return Err(InputError::ResourceLimit);
        }
        let mut bytes = Vec::with_capacity((file_before.size as usize).min(limit));
        file.by_ref()
            .take(limit as u64 + 1)
            .read_to_end(&mut bytes)
            .map_err(|_| InputError::RecordInvalid)?;
        if bytes.len() > limit {
            return Err(InputError::ResourceLimit);
        }

        let file_after = information(&file)?;
        let (_, root_after) = open(root, true).map_err(|_| InputError::ReadRace)?;
        let (_, directory_after) = open(parent, true).map_err(|_| InputError::ReadRace)?;
        if file_before != file_after
            || root_before != root_after
            || directory_before != directory_after
            || file_after.size != bytes.len() as u64
        {
            return Err(InputError::ReadRace);
        }
        Ok(bytes)
    }
}


#[cfg(not(windows))]
mod platform {
    use super::{File, InputError, Path, Read};
    use std::os::unix::fs::{FileTypeExt, MetadataExt, OpenOptionsExt};

    const O_CLOEXEC: i32 = 0x80000;
    const O_NOFOLLOW: i32 = 0x20000;
    const O_NONBLOCK: i32 = 0x800;

    fn identity(metadata: &std::fs::Metadata) -> (u64, u64, u64, i64, i64) {
        (
            metadata.dev(),
            metadata.ino(),
            metadata.len(),
            metadata.mtime(),
            metadata.mtime_nsec(),
        )
    }

    pub fn validate_directory(path: &Path, error: InputError) -> Result<(), InputError> {
        let metadata = std::fs::symlink_metadata(path).map_err(|_| error)?;
        if metadata.file_type().is_symlink() || !metadata.is_dir() {
            return Err(error);
        }
        Ok(())
    }

    pub fn read_stable_file(
        _root: &Path,
        _parent: &Path,
        path: &Path,
        limit: usize,
    ) -> Result<Vec<u8>, InputError> {
        let before = std::fs::symlink_metadata(path).map_err(|_| InputError::RecordInvalid)?;
        if before.file_type().is_symlink()
            || !before.is_file()
            || before.file_type().is_fifo()
            || before.file_type().is_socket()
            || before.file_type().is_block_device()
            || before.file_type().is_char_device()
        {
            return Err(InputError::RecordInvalid);
        }
        let mut file = std::fs::OpenOptions::new()
            .read(true)
            .custom_flags(O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK)
            .open(path)
            .map_err(|_| InputError::RecordInvalid)?;
        let opened = file.metadata().map_err(|_| InputError::RecordInvalid)?;
        if identity(&before) != identity(&opened) {
            return Err(InputError::ReadRace);
        }
        if opened.len() > limit as u64 {
            return Err(InputError::ResourceLimit);
        }
        let mut bytes = Vec::with_capacity((opened.len() as usize).min(limit));
        file.by_ref()
            .take(limit as u64 + 1)
            .read_to_end(&mut bytes)
            .map_err(|_| InputError::RecordInvalid)?;
        let after = file.metadata().map_err(|_| InputError::ReadRace)?;
        if bytes.len() > limit {
            return Err(InputError::ResourceLimit);
        }
        if identity(&opened) != identity(&after) || after.len() != bytes.len() as u64 {
            return Err(InputError::ReadRace);
        }
        Ok(bytes)
    }
}
