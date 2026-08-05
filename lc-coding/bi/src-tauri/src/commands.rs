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
    project: &'static str,
}

fn bind(state: &BindingState, root: PathBuf) -> Result<BindResult, CommandError> {
    state
        .bind_root(&root)
        .map_err(|error| CommandError::new(error.code()))?;
    Ok(BindResult {
        ok: true,
        project: "Bound project",
    })
}

#[tauri::command]
pub fn bind_project(
    state: State<'_, BindingState>,
    project_root: String,
) -> Result<BindResult, CommandError> {
    bind(&state, PathBuf::from(project_root))
}

#[tauri::command]
pub async fn choose_project(
    state: State<'_, BindingState>,
) -> Result<BindResult, CommandError> {
    let selected = tauri::async_runtime::spawn_blocking(crate::native_picker::choose_folder)
        .await
        .map_err(|_| CommandError::new("BI_ROOT_INVALID"))?
        .map_err(|_| CommandError::new("BI_ROOT_INVALID"))?
        .ok_or_else(|| CommandError::new("BI_NO_PROJECT"))?;
    bind(&state, selected)
}

#[tauri::command]
pub async fn get_snapshot(
    state: State<'_, BindingState>,
) -> Result<serde_json::Value, CommandError> {
    state
        .root()
        .map_err(|error| CommandError::new(error.code()))?;
    Err(CommandError::new("BI_PROJECTION_FAILED"))
}
