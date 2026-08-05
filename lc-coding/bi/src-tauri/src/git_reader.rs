use std::fmt;
use std::fs;
use std::path::{Path, PathBuf};


pub const MAX_GIT_BLOB_BYTES: usize = 512 * 1024;


#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum GitReadError {
    RepositoryInvalid,
    IdentityInvalid,
    ResourceLimit,
}

impl GitReadError {
    pub const fn code(self) -> &'static str {
        match self {
            Self::RepositoryInvalid => "BI_GIT_REPOSITORY_INVALID",
            Self::IdentityInvalid => "BI_GIT_IDENTITY_INVALID",
            Self::ResourceLimit => "BI_RESOURCE_LIMIT",
        }
    }
}

impl fmt::Display for GitReadError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.code())
    }
}

impl std::error::Error for GitReadError {}


pub struct GitProject {
    repository: gix::Repository,
}

impl GitProject {
    pub fn open(root: &Path) -> Result<Self, GitReadError> {
        validate_git_layout(root)?;
        let options = gix::open::Options::default()
            .permissions(gix::open::Permissions::isolated())
            .strict_config(true);
        let repository = gix::open_opts(root, options)
            .map_err(|_| GitReadError::RepositoryInvalid)?;
        Ok(Self { repository })
    }

    pub fn read_blob_at(
        &self,
        commit: &str,
        relative_path: &Path,
    ) -> Result<Vec<u8>, GitReadError> {
        if commit.len() != 40 || !commit.bytes().all(|byte| byte.is_ascii_hexdigit()) {
            return Err(GitReadError::IdentityInvalid);
        }
        if relative_path.is_absolute()
            || relative_path
                .components()
                .any(|component| !matches!(component, std::path::Component::Normal(_)))
        {
            return Err(GitReadError::IdentityInvalid);
        }

        let object_id = gix::ObjectId::from_hex(commit.as_bytes())
            .map_err(|_| GitReadError::IdentityInvalid)?;
        let commit = self
            .repository
            .find_commit(object_id)
            .map_err(|_| GitReadError::IdentityInvalid)?;
        let tree = commit.tree().map_err(|_| GitReadError::IdentityInvalid)?;
        let entry = tree
            .lookup_entry_by_path(relative_path)
            .map_err(|_| GitReadError::IdentityInvalid)?
            .ok_or(GitReadError::IdentityInvalid)?;
        if !entry.mode().is_blob() {
            return Err(GitReadError::IdentityInvalid);
        }
        let object = entry
            .object()
            .map_err(|_| GitReadError::IdentityInvalid)?;
        if object.kind != gix::objs::Kind::Blob {
            return Err(GitReadError::IdentityInvalid);
        }
        let mut blob = object.into_blob();
        let data = blob.take_data();
        if data.len() > MAX_GIT_BLOB_BYTES {
            return Err(GitReadError::ResourceLimit);
        }
        Ok(data)
    }
}


fn one_line(bytes: Vec<u8>) -> Result<String, GitReadError> {
    let text = String::from_utf8(bytes).map_err(|_| GitReadError::RepositoryInvalid)?;
    let value = text
        .strip_suffix("\r\n")
        .or_else(|| text.strip_suffix('\n'))
        .ok_or(GitReadError::RepositoryInvalid)?;
    if value.is_empty() || value.contains(['\r', '\n']) {
        return Err(GitReadError::RepositoryInvalid);
    }
    Ok(value.to_owned())
}


fn validate_git_layout(root: &Path) -> Result<(), GitReadError> {
    crate::input::validate_directory_path(root, crate::input::InputError::RootInvalid)
        .map_err(|_| GitReadError::RepositoryInvalid)?;
    let dot_git = root.join(".git");
    let metadata = fs::symlink_metadata(&dot_git)
        .map_err(|_| GitReadError::RepositoryInvalid)?;
    if metadata.is_dir() {
        return crate::input::validate_directory_path(
            &dot_git,
            crate::input::InputError::RootInvalid,
        )
        .map_err(|_| GitReadError::RepositoryInvalid);
    }
    if !metadata.is_file() {
        return Err(GitReadError::RepositoryInvalid);
    }

    let link = one_line(
        crate::input::read_control_file(root, root, &dot_git, 4_096)
            .map_err(|_| GitReadError::RepositoryInvalid)?,
    )?;
    let target = PathBuf::from(
        link.strip_prefix("gitdir: ")
            .ok_or(GitReadError::RepositoryInvalid)?,
    );
    if !target.is_absolute() {
        return Err(GitReadError::RepositoryInvalid);
    }
    let worktrees = target.parent().ok_or(GitReadError::RepositoryInvalid)?;
    if target.file_name().is_none()
        || worktrees.file_name().and_then(|name| name.to_str()) != Some("worktrees")
    {
        return Err(GitReadError::RepositoryInvalid);
    }
    let common = worktrees.parent().ok_or(GitReadError::RepositoryInvalid)?;
    for directory in [&target, worktrees, common] {
        crate::input::validate_directory_path(
            directory,
            crate::input::InputError::RootInvalid,
        )
        .map_err(|_| GitReadError::RepositoryInvalid)?;
    }

    let commondir = one_line(
        crate::input::read_control_file(&target, &target, &target.join("commondir"), 256)
            .map_err(|_| GitReadError::RepositoryInvalid)?,
    )?;
    if commondir != "../.." {
        return Err(GitReadError::RepositoryInvalid);
    }
    let backlink = one_line(
        crate::input::read_control_file(&target, &target, &target.join("gitdir"), 4_096)
            .map_err(|_| GitReadError::RepositoryInvalid)?,
    )?;
    let backlink = PathBuf::from(backlink);
    if !backlink.is_absolute() {
        return Err(GitReadError::RepositoryInvalid);
    }
    let actual = fs::canonicalize(backlink).map_err(|_| GitReadError::RepositoryInvalid)?;
    let expected = fs::canonicalize(dot_git).map_err(|_| GitReadError::RepositoryInvalid)?;
    if actual != expected {
        return Err(GitReadError::RepositoryInvalid);
    }
    Ok(())
}
