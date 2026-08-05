use std::path::PathBuf;

use serde::Serialize;
use tauri::State;

use crate::binding::BindingState;

#[derive(Debug, Serialize)]
pub struct CommandError {
    code: &'static str,
}

impl CommandError {
    const fn new(code: &'static str) -> Self {
        Self { code }
    }
}

#[derive(Debug, Serialize)]
pub struct BindResult {
    ok: bool,
    project: String,
}

async fn bind(state: &BindingState, root: PathBuf) -> Result<BindResult, CommandError> {
    let projection_root = root.clone();
    let snapshot = tauri::async_runtime::spawn_blocking(move || {
        crate::projection::load_project_snapshot(&projection_root)
    })
    .await
    .map_err(|_| CommandError::new("BI_PROJECTION_FAILED"))?
    .map_err(|error| CommandError::new(error.code()))?;
    state
        .bind_root(&root)
        .map_err(|error| CommandError::new(error.code()))?;
    Ok(BindResult {
        ok: true,
        project: snapshot.project,
    })
}

#[tauri::command]
pub async fn bind_project(
    state: State<'_, BindingState>,
    project_root: String,
) -> Result<BindResult, CommandError> {
    bind(&state, PathBuf::from(project_root)).await
}

#[tauri::command]
pub async fn choose_project(state: State<'_, BindingState>) -> Result<BindResult, CommandError> {
    let selected = tauri::async_runtime::spawn_blocking(crate::native_picker::choose_folder)
        .await
        .map_err(|_| CommandError::new("BI_ROOT_INVALID"))?
        .map_err(|_| CommandError::new("BI_ROOT_INVALID"))?
        .ok_or_else(|| CommandError::new("BI_NO_PROJECT"))?;
    bind(&state, selected).await
}

#[tauri::command]
pub async fn get_snapshot(
    state: State<'_, BindingState>,
) -> Result<crate::snapshot::Snapshot, CommandError> {
    let root = state
        .root()
        .map_err(|error| CommandError::new(error.code()))?;
    let snapshot = tauri::async_runtime::spawn_blocking(move || {
        crate::projection::load_project_snapshot(&root)
    })
    .await
    .map_err(|_| CommandError::new("BI_PROJECTION_FAILED"))?
    .map_err(|error| CommandError::new(error.code()))?;
    Ok(snapshot)
}
