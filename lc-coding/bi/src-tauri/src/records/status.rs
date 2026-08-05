use std::collections::HashSet;

use serde::Deserialize;

use super::{RecordError, safe_version, strict_json};

const SUPPORTED_VERSIONS: [&str; 4] = ["2.4.0", "2.4.1", "2.5.0", "2.5.1"];

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum NormalizedState {
    Done,
    Active,
    Pending,
    Error,
}

pub fn normalize_state(value: &str) -> Option<NormalizedState> {
    match value {
        "ACCEPTED"
        | "ALL_REQUIRED_RUNS_ACCEPTED"
        | "CLOSED"
        | "COMPLETE"
        | "COMPLETED"
        | "DELIVERED"
        | "DELIVERY_READY"
        | "DONE"
        | "ESTABLISHED"
        | "EVIDENCED"
        | "INITIALIZED"
        | "INVENTORIED"
        | "LOCKED"
        | "LOOP_OWNER_ACCEPTED"
        | "PASS"
        | "PASSED"
        | "POST_SECURITY_OWNER_ACCEPTED"
        | "READY"
        | "RECONSTRUCTED"
        | "VERIFIED"
        | "VULNERABILITY_CLOSED" => Some(NormalizedState::Done),
        "ACTIVE" | "EXECUTING" | "EXISTING_INTAKE_PENDING" | "IN_PROGRESS" | "RUNNING" => {
            Some(NormalizedState::Active)
        }
        "PENDING" => Some(NormalizedState::Pending),
        "BLOCKED" | "ERROR" | "FAIL" | "FAILED" | "INVALID" | "NOT_CONTINUING" | "REJECTED" => {
            Some(NormalizedState::Error)
        }
        _ => None,
    }
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Candidate {
    pub repository: String,
    pub version: String,
    pub commit: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PhaseGates {
    #[serde(rename = "INITIAL_READY")]
    pub initial_ready: String,
    #[serde(rename = "CALABASH_UPGRADE_READY")]
    pub calabash_upgrade_ready: String,
    #[serde(rename = "ALL_REQUIRED_RUNS_ACCEPTED")]
    pub all_required_runs_accepted: String,
    #[serde(rename = "DELIVERY_READY")]
    pub delivery_ready: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ScopedRefObject {
    pub id: Option<String>,
    pub path: Option<String>,
}

#[derive(Debug, Deserialize)]
#[serde(untagged)]
pub enum ScopedRef {
    Reference(String),
    Object(ScopedRefObject),
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OpenGap {
    pub gap_id: String,
    pub state: String,
    pub source_acceptance: String,
    pub evidence_pointers: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct StatusRecord {
    pub record_role: String,
    pub status_schema_version: String,
    pub project_id: String,
    pub updated_at: String,
    pub initialization_mode: String,
    pub continuity_decision: String,
    pub takeover_readiness: String,
    pub canonical_candidate: Candidate,
    pub existing_project_attestation: String,
    pub existing_project_classification: String,
    pub current_phase: String,
    pub phase_gates: PhaseGates,
    pub proposal: String,
    pub initialization: String,
    pub calabash_draft: String,
    pub workflow: String,
    pub ui: String,
    pub simulation: String,
    pub mandatory_calabash_upgrade: String,
    pub product_baseline: String,
    pub active_slice: Option<ScopedRef>,
    pub integration_baseline: Option<ScopedRef>,
    pub active_runs: Vec<String>,
    pub loop_owner_acceptances: Vec<String>,
    pub open_owner_gaps: Vec<OpenGap>,
    pub all_required_runs_accepted: String,
    pub centralized_security_audit: String,
    pub security_remediation: String,
    pub vulnerability_closure: String,
    pub post_security_owner_acceptance: String,
    pub delivery_method_qa: String,
    pub delivery: String,
    pub last_material_change: String,
    pub next_action: String,
    pub evidence_pointers: Vec<String>,
    pub blockers: Vec<String>,
}

pub fn parse_status(text: &str) -> Result<StatusRecord, RecordError> {
    let status: StatusRecord = strict_json::parse(text)?;
    validate(&status)?;
    Ok(status)
}

fn validate(status: &StatusRecord) -> Result<(), RecordError> {
    if !SUPPORTED_VERSIONS.contains(&status.status_schema_version.as_str()) {
        return Err(RecordError::UnsupportedVersion);
    }
    if status.record_role != "AUTHORITATIVE_PROJECT_STATUS"
        || !safe_project_name(&status.project_id)
        || !matches!(
            status.current_phase.as_str(),
            "INITIAL" | "PRODUCT_FORMATION" | "ENGINEERING_RUNS" | "DELIVERY_PREPARATION"
        )
        || !matches!(status.initialization_mode.as_str(), "NEW" | "EXISTING")
        || !matches!(
            status.continuity_decision.as_str(),
            "PENDING" | "CONTINUE" | "NARROW_REDIRECT" | "HOLD" | "TERMINATE"
        )
        || !matches!(
            status.takeover_readiness.as_str(),
            "NOT_APPLICABLE" | "READY" | "BLOCKED" | "NOT_CONTINUING"
        )
        || !matches!(
            status.existing_project_attestation.as_str(),
            "PENDING" | "NOT_APPLICABLE" | "CLAIMED_UNATTESTED" | "EVIDENCED"
        )
        || !matches!(
            status.existing_project_classification.as_str(),
            "PENDING"
                | "NOT_APPLICABLE"
                | "ATTESTED_COMPLETE"
                | "NEEDS_GAP_CLOSURE"
                | "PARTIAL"
                | "DIRECTION_CHANGED"
                | "NOT_CONTINUING"
        )
    {
        return Err(RecordError::Invalid);
    }

    for value in direct_states(status) {
        if normalize_state(value).is_none() {
            return Err(RecordError::Invalid);
        }
    }
    validate_candidate(&status.canonical_candidate)?;
    for reference in status
        .active_runs
        .iter()
        .chain(&status.loop_owner_acceptances)
        .chain(&status.evidence_pointers)
    {
        if !safe_ref(reference) {
            return Err(RecordError::Invalid);
        }
    }
    for scoped in [&status.active_slice, &status.integration_baseline]
        .into_iter()
        .flatten()
    {
        validate_scoped_ref(scoped)?;
    }
    let mut gaps = HashSet::new();
    for gap in &status.open_owner_gaps {
        if !gaps.insert(&gap.gap_id)
            || !safe_ref(&gap.gap_id)
            || !safe_ref(&gap.source_acceptance)
            || !matches!(gap.state.as_str(), "OPEN" | "IN_CLOSURE")
            || gap.evidence_pointers.is_empty()
            || gap.evidence_pointers.iter().any(|value| !safe_ref(value))
        {
            return Err(RecordError::Invalid);
        }
    }
    if [&status.last_material_change, &status.next_action]
        .into_iter()
        .any(|value| !safe_text(value, 4_096))
        || status.blockers.iter().any(|value| !safe_text(value, 256))
    {
        return Err(RecordError::Invalid);
    }
    Ok(())
}

pub(crate) fn direct_states(status: &StatusRecord) -> [&str; 19] {
    [
        &status.phase_gates.initial_ready,
        &status.phase_gates.calabash_upgrade_ready,
        &status.phase_gates.all_required_runs_accepted,
        &status.phase_gates.delivery_ready,
        &status.proposal,
        &status.initialization,
        &status.calabash_draft,
        &status.workflow,
        &status.ui,
        &status.simulation,
        &status.mandatory_calabash_upgrade,
        &status.product_baseline,
        &status.all_required_runs_accepted,
        &status.centralized_security_audit,
        &status.security_remediation,
        &status.vulnerability_closure,
        &status.post_security_owner_acceptance,
        &status.delivery_method_qa,
        &status.delivery,
    ]
}

fn safe_project_name(value: &str) -> bool {
    let characters: Vec<char> = value.chars().collect();
    if characters.is_empty()
        || characters.len() > 80
        || !characters
            .first()
            .is_some_and(|value| value.is_alphanumeric())
        || !characters
            .last()
            .is_some_and(|value| value.is_alphanumeric())
    {
        return false;
    }
    characters.into_iter().all(|character| {
        character.is_alphanumeric()
            || matches!(
                character,
                ' ' | '-' | '_' | '.' | '(' | ')' | '[' | ']' | '—'
            )
    })
}

fn safe_ref(value: &str) -> bool {
    if value.is_empty() || value.len() > 256 || !value.is_ascii() {
        return false;
    }
    let components: Vec<&str> = value.split('/').collect();
    components.len() <= 16
        && components.iter().all(|component| {
            !component.is_empty()
                && component.len() <= 64
                && component.as_bytes()[0].is_ascii_alphanumeric()
                && component
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'))
        })
}

fn safe_text(value: &str, maximum: usize) -> bool {
    value.len() <= maximum
        && value.chars().all(|character| {
            !character.is_control()
                && !matches!(
                    character,
                    '\u{200e}' | '\u{200f}' | '\u{202a}'..='\u{202e}' | '\u{2066}'..='\u{2069}'
                )
        })
}

fn validate_candidate(candidate: &Candidate) -> Result<(), RecordError> {
    let empty = candidate.repository.is_empty()
        && candidate.version.is_empty()
        && candidate.commit.is_empty();
    if empty {
        return Ok(());
    }
    if candidate.repository.is_empty()
        || candidate.repository.len() > 256
        || !candidate
            .repository
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || b"._~:/@+-".contains(&byte))
        || !safe_version(&candidate.version)
        || !matches!(candidate.commit.len(), 40 | 64)
        || !candidate
            .commit
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit())
    {
        return Err(RecordError::Invalid);
    }
    Ok(())
}

fn validate_scoped_ref(reference: &ScopedRef) -> Result<(), RecordError> {
    match reference {
        ScopedRef::Reference(value) if safe_ref(value) => Ok(()),
        ScopedRef::Object(value) => {
            if value.id.is_none() && value.path.is_none() {
                return Err(RecordError::Invalid);
            }
            if value.id.as_ref().is_some_and(|value| !safe_ref(value))
                || value.path.as_ref().is_some_and(|value| !safe_ref(value))
            {
                return Err(RecordError::Invalid);
            }
            Ok(())
        }
        _ => Err(RecordError::Invalid),
    }
}
