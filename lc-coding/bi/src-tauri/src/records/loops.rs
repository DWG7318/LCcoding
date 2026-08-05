use serde::{Deserialize, Serialize};
use serde_yaml_ng::{Mapping, Value};
use sha2::Digest;

use super::RecordError;

const METRIC_COUNT: usize = 7;
const ALLOWED_INTERVALS: [u8; 3] = [10, 15, 30];

pub const SLK_VERSION: &str = "2.5.0";
pub const SLK_MANIFEST_SHA256: &str =
    "0ce57ffc71ec45f89c44f089e72ea2c02913545fdf765d68776ecaa05c879ea8";
pub const CLK_VERSION: &str = "2.5.0";
pub const CLK_MANIFEST_SHA256: &str =
    "64bbaa498d42b9510e96164dab23ac1b195f75210797244ea1616b3d3fef96ee";
pub const GLK_VERSION: &str = "3.1.0";
pub const GLK_MANIFEST_SHA256: &str =
    "c8d7789f016a950fe1c583859fd25a302ef82242315fe7086035190a0f4fbd66";

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum GovernanceStatus {
    Compliant,
    Active,
    Violation,
    Unknown,
    NotRecorded,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
pub struct GovernanceMetric {
    pub status: GovernanceStatus,
    pub completed: Option<u32>,
    pub total: Option<u32>,
    pub interval_minutes: Option<u8>,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct GovernanceSummary {
    pub metrics: [GovernanceMetric; METRIC_COUNT],
}

#[derive(Clone, Copy, Debug)]
pub struct GlkArtifact<'a> {
    pub path: &'a str,
    pub artifact_type: &'a str,
    pub body: &'a str,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct GlkArtifactRef {
    pub path: String,
    pub sha256: String,
    pub artifact_type: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct SlkIndex {
    schema_version: String,
    record_type: String,
    status: String,
    run_id: String,
    index_version: u64,
    runtime_contract: Value,
    dispatches: Vec<Value>,
    capacity_gates: Vec<Value>,
    wake_traces: Vec<Value>,
    progress_trace: Value,
    patrol_receipts: Vec<Value>,
    evidence_refs: Vec<String>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ClkTrace {
    trace_type: String,
    version: String,
    clock_mode: String,
    run: Value,
    required_sets: Vec<Value>,
    device_capacity_profile: Value,
    engineering_load_snapshots: Vec<Value>,
    cell_capacity_gates: Vec<Value>,
    method_role_capabilities: Vec<Value>,
    pin_observations: Vec<Value>,
    worker_bindings: Vec<Value>,
    patrols: Vec<Value>,
    events: Vec<Value>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct GlkIndex {
    schema_version: String,
    artifact_type: String,
    #[serde(default)]
    artifact_id: Option<String>,
    #[serde(default)]
    run_id: Option<String>,
    #[serde(default)]
    graph_id: Option<String>,
    #[serde(default)]
    graph_version: Option<u64>,
    #[serde(default)]
    candidate_id: Option<String>,
    #[serde(default)]
    candidate_sha256: Option<String>,
    #[serde(default)]
    issuer_binding_ref: Option<String>,
    #[serde(default)]
    execution_context_ref: Option<String>,
    #[serde(default)]
    evidence_refs: Vec<String>,
    #[serde(default)]
    provenance_ref: Option<String>,
    #[serde(default)]
    issued_at: Option<String>,
    #[serde(default)]
    index_id: Option<String>,
    #[serde(default)]
    index_version: Option<u64>,
    #[serde(default)]
    prior_index_sha256: Option<String>,
    formal_artifacts: Vec<GlkIndexEntry>,
    #[serde(default)]
    evidence_objects: Vec<Value>,
    #[serde(default)]
    ledger_heads: Value,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct GlkIndexEntry {
    path: String,
    sha256: String,
    artifact_type: String,
}

fn metric(status: GovernanceStatus) -> GovernanceMetric {
    GovernanceMetric {
        status,
        completed: None,
        total: None,
        interval_minutes: None,
    }
}

fn progress(completed: u32, total: u32) -> Result<GovernanceMetric, RecordError> {
    if total == 0 || completed > total {
        return Err(RecordError::Invalid);
    }
    Ok(GovernanceMetric {
        status: if completed == total {
            GovernanceStatus::Compliant
        } else {
            GovernanceStatus::Active
        },
        completed: Some(completed),
        total: Some(total),
        interval_minutes: None,
    })
}

fn heartbeat(interval: u8, active: bool) -> Result<GovernanceMetric, RecordError> {
    if !ALLOWED_INTERVALS.contains(&interval) {
        return Err(RecordError::Invalid);
    }
    Ok(GovernanceMetric {
        status: if active {
            GovernanceStatus::Active
        } else {
            GovernanceStatus::Compliant
        },
        completed: None,
        total: None,
        interval_minutes: Some(interval),
    })
}

fn mapping(value: &Value) -> Result<&Mapping, RecordError> {
    value.as_mapping().ok_or(RecordError::Invalid)
}

fn field<'a>(value: &'a Value, key: &str) -> Result<&'a Value, RecordError> {
    mapping(value)?
        .get(Value::String(key.to_owned()))
        .ok_or(RecordError::Invalid)
}

fn text<'a>(value: &'a Value, key: &str) -> Result<&'a str, RecordError> {
    field(value, key)?.as_str().ok_or(RecordError::Invalid)
}

fn count(value: &Value, key: &str) -> Result<u32, RecordError> {
    field(value, key)?
        .as_u64()
        .and_then(|number| u32::try_from(number).ok())
        .ok_or(RecordError::Invalid)
}

fn interval(value: &Value, key: &str) -> Result<u8, RecordError> {
    field(value, key)?
        .as_u64()
        .and_then(|number| u8::try_from(number).ok())
        .ok_or(RecordError::Invalid)
}

fn clear_check(values: &[Value], id: &str) -> GovernanceStatus {
    let result = values.iter().find_map(|value| {
        let matches =
            text(value, "check_id").ok() == Some(id) || text(value, "check_kind").ok() == Some(id);
        matches.then(|| text(value, "result").ok())?
    });
    match result {
        Some("CLEAR" | "NORMAL") => GovernanceStatus::Compliant,
        Some(_) => GovernanceStatus::Violation,
        None => GovernanceStatus::Unknown,
    }
}

fn yaml<T: for<'de> Deserialize<'de>>(body: &str) -> Result<T, RecordError> {
    if body.len() > crate::input::MAX_RECORD_BYTES {
        return Err(RecordError::Invalid);
    }
    let mut line_count = 0usize;
    for line in body.lines() {
        line_count += 1;
        if line_count > 16_384 || line.len() > 4_096 {
            return Err(RecordError::Invalid);
        }
        let indentation = line.bytes().take_while(|byte| *byte == b' ').count();
        let trimmed = line.trim_start();
        if indentation > 64
            || trimmed.starts_with("<<:")
            || trimmed.contains(": &")
            || trimmed.contains(": *")
            || trimmed.contains(": !")
            || trimmed.starts_with("- &")
            || trimmed.starts_with("- *")
            || trimmed.starts_with("- !")
        {
            return Err(RecordError::Invalid);
        }
    }
    serde_yaml_ng::from_str(body).map_err(|_| RecordError::Invalid)
}

pub fn glk_artifact_refs(index_body: &str) -> Result<Vec<GlkArtifactRef>, RecordError> {
    let index: GlkIndex = yaml(index_body)?;
    if index.schema_version != GLK_VERSION || index.artifact_type != "RUN_PACKAGE_INDEX" {
        return Err(RecordError::UnsupportedVersion);
    }
    if index.formal_artifacts.is_empty() || index.formal_artifacts.len() > 128 {
        return Err(RecordError::Invalid);
    }
    index
        .formal_artifacts
        .into_iter()
        .map(|entry| {
            if entry.path.is_empty()
                || entry.sha256.len() != 64
                || !entry.sha256.bytes().all(|byte| byte.is_ascii_hexdigit())
                || entry.artifact_type.is_empty()
            {
                return Err(RecordError::Invalid);
            }
            Ok(GlkArtifactRef {
                path: entry.path,
                sha256: entry.sha256,
                artifact_type: entry.artifact_type,
            })
        })
        .collect()
}

pub fn parse_slk_governance(body: &str) -> Result<GovernanceSummary, RecordError> {
    let record: SlkIndex = yaml(body)?;
    if record.schema_version != SLK_VERSION
        || record.record_type != "RUN_RUNTIME_INDEX"
        || record.status != "COMPLETE"
        || record.run_id.is_empty()
        || record.index_version == 0
        || !record.runtime_contract.is_mapping()
        || record.dispatches.is_empty()
        || record.evidence_refs.is_empty()
    {
        return Err(RecordError::UnsupportedVersion);
    }

    let attempts = record
        .wake_traces
        .first()
        .and_then(|trace| field(trace, "attempts").ok())
        .and_then(Value::as_sequence)
        .ok_or(RecordError::Invalid)?;
    let levels: Vec<u64> = attempts
        .iter()
        .map(|attempt| {
            field(attempt, "level").and_then(|level| level.as_u64().ok_or(RecordError::Invalid))
        })
        .collect::<Result<_, _>>()?;
    let levels_are_bounded = !levels.is_empty()
        && levels.len() <= 4
        && levels
            .iter()
            .enumerate()
            .all(|(index, level)| *level == (index + 1) as u64)
        && attempts
            .iter()
            .all(|attempt| count(attempt, "wait_seconds").is_ok_and(|seconds| seconds <= 120));
    let trace_status = record
        .wake_traces
        .first()
        .and_then(|trace| text(trace, "status").ok());
    let wake = GovernanceMetric {
        status: if levels_are_bounded
            && matches!(trace_status, Some("ACKNOWLEDGED" | "PROCESSING_STARTED"))
        {
            GovernanceStatus::Compliant
        } else if levels_are_bounded && trace_status == Some("PENDING_WAKE_WRITTEN") {
            GovernanceStatus::Active
        } else {
            GovernanceStatus::Violation
        },
        completed: Some(4),
        total: Some(4),
        interval_minutes: None,
    };

    let patrol = record.patrol_receipts.first().ok_or(RecordError::Invalid)?;
    if count(patrol, "heartbeat_count")? != 1 {
        return Err(RecordError::Invalid);
    }
    let checks = field(patrol, "checklist")?
        .as_sequence()
        .ok_or(RecordError::Invalid)?;
    let heartbeat = heartbeat(
        interval(patrol, "interval_minutes")?,
        text(patrol, "run_state")? != "LOOP_TERMINAL",
    )?;
    let progress_events = field(&record.progress_trace, "events")?
        .as_sequence()
        .ok_or(RecordError::Invalid)?;
    let latest_progress = progress_events.last().ok_or(RecordError::Invalid)?;
    let progress_metric = progress(
        count(latest_progress, "accepted_cell_count")?,
        count(latest_progress, "required_cell_total")?,
    )?;
    let capacity = if record.capacity_gates.is_empty() {
        GovernanceStatus::NotRecorded
    } else if record.capacity_gates.iter().all(|gate| {
        text(gate, "result").ok() == Some("PASS")
            || field(gate, "decision")
                .and_then(|decision| text(decision, "outcome"))
                .ok()
                == Some("PASS")
    }) {
        GovernanceStatus::Compliant
    } else {
        GovernanceStatus::Violation
    };

    Ok(GovernanceSummary {
        metrics: [
            wake,
            metric(clear_check(checks, "SUPERVISOR_WAIT")),
            heartbeat,
            metric(clear_check(checks, "SUBAGENT_EVIDENCE")),
            progress_metric,
            metric(capacity),
            metric(clear_check(checks, "THREAD_PIN")),
        ],
    })
}

pub fn parse_clk_governance(body: &str) -> Result<GovernanceSummary, RecordError> {
    let trace: ClkTrace = yaml(body)?;
    if trace.version != CLK_VERSION
        || trace.trace_type != "CLK_RUN_CONTROL_TRACE"
        || trace.clock_mode != "INJECTED_MINUTES"
        || !trace.run.is_mapping()
        || trace.required_sets.is_empty()
        || !trace.device_capacity_profile.is_mapping()
        || trace.engineering_load_snapshots.is_empty()
        || trace.worker_bindings.is_empty()
        || trace.method_role_capabilities.len() != 4
    {
        return Err(RecordError::UnsupportedVersion);
    }

    let wake_levels: Vec<u64> = trace
        .events
        .iter()
        .filter(|event| text(event, "action").ok() == Some("WAKE_ATTEMPT"))
        .map(|event| {
            field(event, "data")
                .and_then(|data| field(data, "level"))
                .and_then(|level| level.as_u64().ok_or(RecordError::Invalid))
        })
        .collect::<Result<_, _>>()?;
    let patrol = trace.patrols.first().ok_or(RecordError::Invalid)?;
    if count(patrol, "heartbeat_count")? != 1
        || field(patrol, "set_thread_pinned")?.as_bool() != Some(false)
    {
        return Err(RecordError::Invalid);
    }
    let patrol_event = trace
        .events
        .iter()
        .find(|event| text(event, "action").ok() == Some("PATROL_STATUS"))
        .ok_or(RecordError::Invalid)?;
    let patrol_data = field(patrol_event, "data")?;
    let patrol_checks = field(patrol_data, "checks")?
        .as_sequence()
        .ok_or(RecordError::Invalid)?;
    let clear = |name: &str| {
        if text(patrol_data, "status").ok() == Some("CLEAR")
            && patrol_checks
                .iter()
                .any(|value| value.as_str() == Some(name))
        {
            GovernanceStatus::Compliant
        } else {
            GovernanceStatus::Violation
        }
    };
    let progress_event = trace
        .events
        .iter()
        .rev()
        .find(|event| text(event, "action").ok() == Some("SUPERVISOR_PROGRESS"))
        .ok_or(RecordError::Invalid)?;
    let progress_data = field(progress_event, "data")?;
    let capacity = if trace.cell_capacity_gates.is_empty() {
        GovernanceStatus::NotRecorded
    } else if trace
        .cell_capacity_gates
        .iter()
        .all(|gate| text(gate, "result").ok() == Some("PASS"))
    {
        GovernanceStatus::Compliant
    } else {
        GovernanceStatus::Violation
    };
    let pin = if trace.method_role_capabilities.iter().all(|role| {
        field(role, "set_thread_pinned")
            .ok()
            .and_then(Value::as_bool)
            == Some(false)
    }) && trace.pin_observations.is_empty()
    {
        GovernanceStatus::Compliant
    } else {
        GovernanceStatus::Violation
    };

    Ok(GovernanceSummary {
        metrics: [
            GovernanceMetric {
                status: if wake_levels == [1, 2, 3, 4] {
                    GovernanceStatus::Compliant
                } else {
                    GovernanceStatus::Violation
                },
                completed: Some(
                    u32::try_from(wake_levels.len()).map_err(|_| RecordError::Invalid)?,
                ),
                total: Some(4),
                interval_minutes: None,
            },
            metric(clear("SUPERVISOR_WAIT")),
            heartbeat(
                interval(patrol, "interval_minutes")?,
                text(patrol, "heartbeat_state")? == "ACTIVE",
            )?,
            metric(clear("SUBAGENT_EVIDENCE")),
            progress(
                count(progress_data, "current_level_verified_go_count")?,
                count(progress_data, "current_level_required_go_total")?,
            )?,
            metric(capacity),
            metric(
                if clear("THREAD_PIN_PROVENANCE") == GovernanceStatus::Compliant {
                    pin
                } else {
                    GovernanceStatus::Violation
                },
            ),
        ],
    })
}

pub fn parse_glk_governance(
    index_body: &str,
    artifacts: &[GlkArtifact<'_>],
) -> Result<GovernanceSummary, RecordError> {
    let index: GlkIndex = yaml(index_body)?;
    if index.schema_version != GLK_VERSION || index.artifact_type != "RUN_PACKAGE_INDEX" {
        return Err(RecordError::UnsupportedVersion);
    }
    let _identity_fields = (
        index.artifact_id,
        index.run_id,
        index.graph_id,
        index.graph_version,
        index.candidate_id,
        index.candidate_sha256,
        index.issuer_binding_ref,
        index.execution_context_ref,
        index.evidence_refs,
        index.provenance_ref,
        index.issued_at,
        index.index_id,
        index.index_version,
        index.prior_index_sha256,
        index.evidence_objects,
        index.ledger_heads,
    );
    for entry in &index.formal_artifacts {
        if entry.path.is_empty() || entry.sha256.len() != 64 || entry.artifact_type.is_empty() {
            return Err(RecordError::Invalid);
        }
    }
    let matching = |kind: &str| -> Result<Vec<Value>, RecordError> {
        let entries: Vec<&GlkIndexEntry> = index
            .formal_artifacts
            .iter()
            .filter(|entry| entry.artifact_type == kind)
            .collect();
        if entries.is_empty() {
            return Err(RecordError::Invalid);
        }
        entries
            .into_iter()
            .map(|entry| {
                let artifact = artifacts
                    .iter()
                    .find(|artifact| artifact.artifact_type == kind && artifact.path == entry.path)
                    .ok_or(RecordError::Invalid)?;
                let actual = format!("{:x}", sha2::Sha256::digest(artifact.body.as_bytes()));
                if actual != entry.sha256 {
                    return Err(RecordError::Invalid);
                }
                let value: Value = yaml(artifact.body)?;
                if text(&value, "schema_version")? != "3.1.0"
                    || text(&value, "artifact_type")? != kind
                {
                    return Err(RecordError::UnsupportedVersion);
                }
                Ok(value)
            })
            .collect()
    };
    let artifact = |kind: &str| -> Result<Value, RecordError> {
        let mut values = matching(kind)?;
        if values.len() != 1 {
            return Err(RecordError::Invalid);
        }
        Ok(values.remove(0))
    };
    let monitor = artifact("MONITOR_CONTROL")?;
    let progress_record = artifact("CHECKER_PROGRESS_EVENT")?;
    let capacity_record = artifact("CELL_CAPACITY_GATE")?;
    let checks = field(&monitor, "patrol_checklist")?
        .as_sequence()
        .ok_or(RecordError::Invalid)?;
    let wake_attempts = matching("WAKE_ATTEMPT")?;
    let wake_levels = wake_attempts
        .iter()
        .map(|attempt| count(attempt, "level").map(u64::from))
        .collect::<Result<Vec<_>, _>>()?;
    let wake_status = if wake_levels == [1, 2, 3, 4]
        && wake_attempts.iter().all(|attempt| {
            count(attempt, "timeout_seconds").ok() == Some(120)
                && text(attempt, "outcome").ok() == Some("ACKNOWLEDGED")
        }) {
        GovernanceStatus::Compliant
    } else {
        GovernanceStatus::Violation
    };

    Ok(GovernanceSummary {
        metrics: [
            GovernanceMetric {
                status: wake_status,
                completed: Some(
                    u32::try_from(wake_levels.len()).map_err(|_| RecordError::Invalid)?,
                ),
                total: Some(4),
                interval_minutes: None,
            },
            metric(clear_check(checks, "SUPERVISOR_WAIT")),
            heartbeat(
                interval(&monitor, "patrol_interval_minutes")?,
                text(&monitor, "monitor_state")? == "MONITOR_ACTIVE",
            )?,
            metric(clear_check(checks, "SUBAGENT_EVIDENCE")),
            progress(
                count(&progress_record, "accepted_cell_count")?,
                count(&progress_record, "required_cell_count")?,
            )?,
            metric(if text(&capacity_record, "result")? == "PASS" {
                GovernanceStatus::Compliant
            } else {
                GovernanceStatus::Violation
            }),
            metric(clear_check(checks, "THREAD_PIN")),
        ],
    })
}
