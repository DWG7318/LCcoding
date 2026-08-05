use std::path::PathBuf;


#[cfg(windows)]
pub fn choose_folder() -> Result<Option<PathBuf>, ()> {
    use windows::Win32::Foundation::ERROR_CANCELLED;
    use windows::Win32::System::Com::{
        CLSCTX_INPROC_SERVER, COINIT_APARTMENTTHREADED, CoCreateInstance, CoInitializeEx,
        CoTaskMemFree, CoUninitialize,
    };
    use windows::Win32::UI::Shell::{
        FOS_FORCEFILESYSTEM, FOS_PATHMUSTEXIST, FOS_PICKFOLDERS, FileOpenDialog,
        IFileOpenDialog, SIGDN_FILESYSPATH,
    };

    struct ComApartment;
    impl Drop for ComApartment {
        fn drop(&mut self) {
            unsafe { CoUninitialize() };
        }
    }

    unsafe {
        CoInitializeEx(None, COINIT_APARTMENTTHREADED)
            .ok()
            .map_err(|_| ())?;
        let _apartment = ComApartment;
        let dialog: IFileOpenDialog =
            CoCreateInstance(&FileOpenDialog, None, CLSCTX_INPROC_SERVER).map_err(|_| ())?;
        let options = dialog.GetOptions().map_err(|_| ())?;
        dialog
            .SetOptions(options | FOS_PICKFOLDERS | FOS_FORCEFILESYSTEM | FOS_PATHMUSTEXIST)
            .map_err(|_| ())?;
        if let Err(error) = dialog.Show(None) {
            if error.code() == windows::core::HRESULT::from_win32(ERROR_CANCELLED.0) {
                return Ok(None);
            }
            return Err(());
        }
        let item = dialog.GetResult().map_err(|_| ())?;
        let display = item.GetDisplayName(SIGDN_FILESYSPATH).map_err(|_| ())?;
        let text = display.to_string().map_err(|_| ())?;
        CoTaskMemFree(Some(display.0.cast()));
        Ok(Some(PathBuf::from(text)))
    }
}

#[cfg(not(windows))]
pub fn choose_folder() -> Result<Option<PathBuf>, ()> {
    Err(())
}
