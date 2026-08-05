use std::ffi::{OsStr, OsString};
use std::path::{Path, PathBuf};
use std::sync::Mutex;

pub use crate::errors::BindError;


#[derive(Debug, Eq, PartialEq)]
pub enum LaunchRequest {
    Unbound,
    Project(PathBuf),
}

pub fn parse_launch_args<I, S>(arguments: I) -> Result<LaunchRequest, BindError>
where
    I: IntoIterator<Item = S>,
    S: Into<OsString>,
{
    let mut values = arguments.into_iter().map(Into::into);
    if values.next().is_none() {
        return Err(BindError::ArgumentInvalid);
    }
    let remaining: Vec<OsString> = values.collect();
    match remaining.as_slice() {
        [] => Ok(LaunchRequest::Unbound),
        [flag, root] if flag == OsStr::new("--project") && !root.is_empty() => {
            Ok(LaunchRequest::Project(PathBuf::from(root)))
        }
        _ => Err(BindError::ArgumentInvalid),
    }
}

#[derive(Debug)]
struct BoundProject {
    root: PathBuf,
}

#[derive(Debug, Default)]
pub struct BindingState {
    project: Mutex<Option<BoundProject>>,
}

impl BindingState {
    pub fn bind_root(&self, requested_root: &Path) -> Result<(), BindError> {
        if self.is_bound() {
            return Err(BindError::ProjectAlreadyBound);
        }
        crate::input::validate_project_root(requested_root)
            .map_err(|_| BindError::RootInvalid)?;
        let root = requested_root
            .canonicalize()
            .map_err(|_| BindError::RootInvalid)?;
        if !root.is_dir() {
            return Err(BindError::RootInvalid);
        }

        let mut project = self.project.lock().unwrap_or_else(|poisoned| poisoned.into_inner());
        if project.is_some() {
            return Err(BindError::ProjectAlreadyBound);
        }
        *project = Some(BoundProject { root });
        Ok(())
    }

    pub fn is_bound(&self) -> bool {
        self.project
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner())
            .is_some()
    }

    pub(crate) fn root(&self) -> Result<PathBuf, BindError> {
        self.project
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner())
            .as_ref()
            .map(|project| project.root.clone())
            .ok_or(BindError::ProjectNotBound)
    }
}
