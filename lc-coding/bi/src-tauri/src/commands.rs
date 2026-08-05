use std::future::Future;
use std::path::PathBuf;
use std::sync::Mutex;
use std::sync::atomic::{AtomicU64, Ordering};

use futures_util::future::{BoxFuture, FutureExt, Shared};
use serde::Serialize;
use tauri::State;

use crate::binding::BindingState;

#[derive(Clone, Debug, Serialize)]
pub struct CommandError {
    code: &'static str,
}

struct Flight<T, E> {
    id: u64,
    future: Shared<BoxFuture<'static, Result<T, E>>>,
}

pub struct SingleFlight<T, E> {
    active: Mutex<Option<Flight<T, E>>>,
    next_id: AtomicU64,
}

impl<T, E> Default for SingleFlight<T, E> {
    fn default() -> Self {
        Self {
            active: Mutex::new(None),
            next_id: AtomicU64::new(1),
        }
    }
}

impl<T, E> SingleFlight<T, E>
where
    T: Clone + Send + 'static,
    E: Clone + Send + 'static,
{
    pub async fn run<F, Fut>(&self, operation: F) -> Result<T, E>
    where
        F: FnOnce() -> Fut,
        Fut: Future<Output = Result<T, E>> + Send + 'static,
    {
        let (id, future) = {
            let mut active = self
                .active
                .lock()
                .unwrap_or_else(|poisoned| poisoned.into_inner());
            if let Some(flight) = active.as_ref() {
                (flight.id, flight.future.clone())
            } else {
                let id = self.next_id.fetch_add(1, Ordering::Relaxed);
                let future = operation().boxed().shared();
                *active = Some(Flight {
                    id,
                    future: future.clone(),
                });
                (id, future)
            }
        };

        let result = future.await;
        let mut active = self
            .active
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner());
        if active.as_ref().is_some_and(|flight| flight.id == id) {
            *active = None;
        }
        result
    }
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
    flight: State<'_, SingleFlight<crate::snapshot::Snapshot, CommandError>>,
) -> Result<crate::snapshot::Snapshot, CommandError> {
    let root = state
        .root()
        .map_err(|error| CommandError::new(error.code()))?;
    flight
        .run(move || async move {
            tauri::async_runtime::spawn_blocking(move || {
                crate::projection::load_project_snapshot(&root)
            })
            .await
            .map_err(|_| CommandError::new("BI_PROJECTION_FAILED"))?
            .map_err(|error| CommandError::new(error.code()))
        })
        .await
}
