use std::collections::HashSet;

use serde::{Deserialize, Deserializer};

use super::{RecordError, compatibility::embedded_compatibility_asset, safe_version, strict_json};

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

#[derive(Debug)]
enum Present<T> {
    Missing,
    Value(T),
}

impl<T> Default for Present<T> {
    fn default() -> Self {
        Self::Missing
    }
}

impl<'de, T: Deserialize<'de>> Deserialize<'de> for Present<T> {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        T::deserialize(deserializer).map(Self::Value)
    }
}

impl<T> Present<T> {
    fn value(&self) -> Option<&T> {
        match self {
            Self::Missing => None,
            Self::Value(value) => Some(value),
        }
    }
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Candidate {
    pub repository: String,
    pub version: String,
    pub commit: String,
    #[serde(default)]
    candidate_id: Present<String>,
    #[serde(default)]
    candidate_hash: Present<String>,
}

impl Candidate {
    fn candidate_id(&self) -> Option<&str> {
        self.candidate_id.value().map(String::as_str)
    }

    fn candidate_hash(&self) -> Option<&str> {
        self.candidate_hash.value().map(String::as_str)
    }
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AgentProductFormation {
    pub state: String,
    pub product_agent_applicability: String,
    pub calabash_definition_handoff_id: String,
    pub calabash_definition_handoff_hash: String,
    pub configuration_baseline_id: String,
    pub configuration_baseline_hash: String,
    pub product_agent_capability_state: String,
    pub operations_agent_state: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AgentSliceIntegration {
    pub state: String,
    pub candidate_id: String,
    pub candidate_hash: String,
    pub product_baseline_id: String,
    pub product_baseline_hash: String,
    pub configuration_baseline_id: String,
    pub configuration_baseline_hash: String,
    pub production_topology_id: String,
    pub production_topology_hash: String,
    pub runtime_adapter_attestation_id: String,
    pub runtime_adapter_attestation_hash: String,
    pub runtime_adapter_id: String,
    pub runtime_adapter_version: String,
    pub dual_agent_isolation_state: String,
    pub product_agent_applicability: String,
    pub product_integration_state: String,
    pub product_agent_integration_state: String,
    pub operations_agent_integration_state: String,
    pub accepted_product_slice_ids: Vec<String>,
    pub accepted_operations_slice_ids: Vec<String>,
    pub required_operations_slice_id: String,
    pub current_product_slice_reference: String,
    pub product_verification_reference: String,
    pub current_operations_slice_reference: String,
    pub operations_verification_reference: String,
    pub integration_baseline_reference: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct VulnerabilityClosureState {
    pub state: String,
    pub candidate_id: String,
    pub candidate_hash: String,
    pub current_receipt_id: String,
    pub current_receipt_reference: String,
    pub superseded_receipt_id: String,
    pub superseded_receipt_reference: String,
    pub superseded_candidate_id: String,
    pub superseded_candidate_hash: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PostSecurityOwnerAcceptanceState {
    pub state: String,
    pub candidate_id: String,
    pub candidate_hash: String,
    pub current_acceptance_id: String,
    pub current_acceptance_reference: String,
    pub vulnerability_closure_receipt_id: String,
    pub vulnerability_closure_receipt_reference: String,
    pub superseded_acceptance_id: String,
    pub superseded_acceptance_reference: String,
    pub superseded_candidate_id: String,
    pub superseded_candidate_hash: String,
}

#[derive(Debug, Deserialize)]
#[serde(untagged)]
pub enum VulnerabilityClosure {
    Legacy(String),
    Current(VulnerabilityClosureState),
}

impl VulnerabilityClosure {
    pub fn state(&self) -> &str {
        match self {
            Self::Legacy(state) => state,
            Self::Current(record) => &record.state,
        }
    }
}

#[derive(Debug, Deserialize)]
#[serde(untagged)]
pub enum PostSecurityOwnerAcceptance {
    Legacy(String),
    Current(PostSecurityOwnerAcceptanceState),
}

impl PostSecurityOwnerAcceptance {
    pub fn state(&self) -> &str {
        match self {
            Self::Legacy(state) => state,
            Self::Current(record) => &record.state,
        }
    }
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
    #[serde(default)]
    agent_product_formation: Present<AgentProductFormation>,
    #[serde(default)]
    agent_slice_integration: Present<AgentSliceIntegration>,
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
    pub vulnerability_closure: VulnerabilityClosure,
    pub post_security_owner_acceptance: PostSecurityOwnerAcceptance,
    pub delivery_method_qa: String,
    pub delivery: String,
    pub last_material_change: String,
    pub next_action: String,
    pub evidence_pointers: Vec<String>,
    pub blockers: Vec<String>,
}

impl StatusRecord {
    pub fn agent_product_formation(&self) -> Option<&AgentProductFormation> {
        self.agent_product_formation.value()
    }

    pub fn agent_slice_integration(&self) -> Option<&AgentSliceIntegration> {
        self.agent_slice_integration.value()
    }
}

pub fn parse_status(text: &str) -> Result<StatusRecord, RecordError> {
    let status: StatusRecord = strict_json::parse(text)?;
    validate(&status)?;
    Ok(status)
}

fn validate(status: &StatusRecord) -> Result<(), RecordError> {
    let compatibility = embedded_compatibility_asset()?;
    let phase_layout = compatibility
        .status_phase_steps(&status.status_schema_version)
        .ok_or(RecordError::UnsupportedVersion)?;
    if status.record_role != "AUTHORITATIVE_PROJECT_STATUS"
        || !safe_project_name(&status.project_id)
        || !phase_layout
            .iter()
            .any(|phase| phase.phase_id == status.current_phase)
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
    validate_candidate(&status.canonical_candidate, &status.status_schema_version)?;
    validate_agent_state(status)?;
    match &status.vulnerability_closure {
        VulnerabilityClosure::Legacy(_) if status.status_schema_version == "2.6.0" => {}
        VulnerabilityClosure::Current(value) => validate_security_identity(value)?,
        _ => return Err(RecordError::Invalid),
    }
    match &status.post_security_owner_acceptance {
        PostSecurityOwnerAcceptance::Legacy(_) if status.status_schema_version == "2.6.0" => {}
        PostSecurityOwnerAcceptance::Current(value) => validate_post_security_identity(value)?,
        _ => return Err(RecordError::Invalid),
    }
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
        status.vulnerability_closure.state(),
        status.post_security_owner_acceptance.state(),
        &status.delivery_method_qa,
        &status.delivery,
    ]
}

fn validate_agent_state(status: &StatusRecord) -> Result<(), RecordError> {
    match status.status_schema_version.as_str() {
        "2.6.0" | "2.7.0" => {
            if status.agent_product_formation().is_some()
                || status.agent_slice_integration().is_some()
            {
                return Err(RecordError::Invalid);
            }
        }
        "2.8.0" => {
            let formation = status
                .agent_product_formation()
                .ok_or(RecordError::Invalid)?;
            let integration = status
                .agent_slice_integration()
                .ok_or(RecordError::Invalid)?;
            validate_agent_product_formation(formation)?;
            validate_agent_slice_integration(status, formation, integration)?;
        }
        _ => return Err(RecordError::UnsupportedVersion),
    }
    Ok(())
}

fn validate_agent_product_formation(value: &AgentProductFormation) -> Result<(), RecordError> {
    if value.state == "UNPROVED" {
        if value.product_agent_applicability == "UNPROVED"
            && value.calabash_definition_handoff_id == "NOT_APPLICABLE"
            && value.calabash_definition_handoff_hash == "NOT_APPLICABLE"
            && value.configuration_baseline_id == "NOT_APPLICABLE"
            && value.configuration_baseline_hash == "NOT_APPLICABLE"
            && value.product_agent_capability_state == "UNPROVED"
            && value.operations_agent_state == "UNPROVED"
        {
            return Ok(());
        }
        return Err(RecordError::Invalid);
    }
    let capability_matches = match value.product_agent_applicability.as_str() {
        "NOT_APPLICABLE" => value.product_agent_capability_state == "NOT_APPLICABLE",
        "APPLICABLE_EXTRA" => matches!(
            value.product_agent_capability_state.as_str(),
            "UNIMPLEMENTED_EXTRA" | "REAL_RUNNABLE_EXTRA"
        ),
        "APPLICABLE_CORE" => value.product_agent_capability_state == "REAL_RUNNABLE_CORE",
        _ => false,
    };
    if value.state != "PRODUCT_FORMATION_AGENT_BOUND"
        || !capability_matches
        || value.operations_agent_state != "PREPARED_NOT_INTEGRATED"
        || !safe_identity(&value.calabash_definition_handoff_id)
        || !safe_sha256(&value.calabash_definition_handoff_hash)
        || !safe_identity(&value.configuration_baseline_id)
        || !safe_sha256(&value.configuration_baseline_hash)
    {
        return Err(RecordError::Invalid);
    }
    Ok(())
}

fn validate_agent_slice_integration(
    status: &StatusRecord,
    formation: &AgentProductFormation,
    value: &AgentSliceIntegration,
) -> Result<(), RecordError> {
    if value.state == "UNPROVED" {
        if value.candidate_id == "NOT_APPLICABLE"
            && value.candidate_hash == "NOT_APPLICABLE"
            && value.product_baseline_id == "NOT_APPLICABLE"
            && value.product_baseline_hash == "NOT_APPLICABLE"
            && value.configuration_baseline_id == "NOT_APPLICABLE"
            && value.configuration_baseline_hash == "NOT_APPLICABLE"
            && value.production_topology_id == "NOT_APPLICABLE"
            && value.production_topology_hash == "NOT_APPLICABLE"
            && value.runtime_adapter_attestation_id == "NOT_APPLICABLE"
            && value.runtime_adapter_attestation_hash == "NOT_APPLICABLE"
            && value.runtime_adapter_id == "NOT_APPLICABLE"
            && value.runtime_adapter_version == "NOT_APPLICABLE"
            && value.dual_agent_isolation_state == "UNPROVED"
            && value.product_agent_applicability == "UNPROVED"
            && value.product_integration_state == "UNPROVED"
            && value.product_agent_integration_state == "UNPROVED"
            && value.operations_agent_integration_state == "UNPROVED"
            && value.accepted_product_slice_ids.is_empty()
            && value.accepted_operations_slice_ids.is_empty()
            && value.required_operations_slice_id == "NOT_APPLICABLE"
            && value.current_product_slice_reference == "NOT_APPLICABLE"
            && value.product_verification_reference == "NOT_APPLICABLE"
            && value.current_operations_slice_reference == "NOT_APPLICABLE"
            && value.operations_verification_reference == "NOT_APPLICABLE"
            && value.integration_baseline_reference == "NOT_APPLICABLE"
        {
            return Ok(());
        }
        return Err(RecordError::Invalid);
    }

    let id_values = [
        &value.candidate_id,
        &value.product_baseline_id,
        &value.configuration_baseline_id,
        &value.production_topology_id,
        &value.runtime_adapter_attestation_id,
        &value.runtime_adapter_id,
        &value.required_operations_slice_id,
    ];
    let hash_values = [
        &value.candidate_hash,
        &value.product_baseline_hash,
        &value.configuration_baseline_hash,
        &value.production_topology_hash,
        &value.runtime_adapter_attestation_hash,
    ];
    let references = [
        &value.current_product_slice_reference,
        &value.product_verification_reference,
        &value.current_operations_slice_reference,
        &value.operations_verification_reference,
        &value.integration_baseline_reference,
    ];
    let product_ids =
        closed_identity_set(&value.accepted_product_slice_ids).ok_or(RecordError::Invalid)?;
    let operations_ids =
        closed_identity_set(&value.accepted_operations_slice_ids).ok_or(RecordError::Invalid)?;
    let expected_product_agent = if value.product_agent_applicability == "NOT_APPLICABLE" {
        "NOT_APPLICABLE"
    } else {
        "ACCEPTED"
    };
    if value.state != "AGENT_SLICES_ACCEPTED"
        || formation.state != "PRODUCT_FORMATION_AGENT_BOUND"
        || id_values.iter().any(|identity| !safe_identity(identity))
        || hash_values.iter().any(|hash| !safe_sha256(hash))
        || !semantic_version(&value.runtime_adapter_version)
        || value.dual_agent_isolation_state != "VERIFIED"
        || value.product_agent_applicability != formation.product_agent_applicability
        || value.product_integration_state != "ACCEPTED"
        || value.product_agent_integration_state != expected_product_agent
        || value.operations_agent_integration_state != "ACCEPTED"
        || status.canonical_candidate.candidate_id() != Some(value.candidate_id.as_str())
        || status.canonical_candidate.candidate_hash() != Some(value.candidate_hash.as_str())
        || value.configuration_baseline_id != formation.configuration_baseline_id
        || value.configuration_baseline_hash != formation.configuration_baseline_hash
        || !operations_ids.contains(value.required_operations_slice_id.as_str())
        || product_ids
            .iter()
            .any(|identity| operations_ids.contains(identity))
        || references
            .iter()
            .any(|reference| *reference == "NOT_APPLICABLE" || !safe_ref(reference))
        || references.iter().collect::<HashSet<_>>().len() != references.len()
    {
        return Err(RecordError::Invalid);
    }
    Ok(())
}

fn closed_identity_set(values: &[String]) -> Option<HashSet<&str>> {
    if values.is_empty() || values.iter().any(|value| !safe_identity(value)) {
        return None;
    }
    let unique: HashSet<&str> = values.iter().map(String::as_str).collect();
    (unique.len() == values.len()).then_some(unique)
}

fn safe_identity(value: &str) -> bool {
    const GENERIC: [&str; 9] = [
        "NONE",
        "PENDING",
        "UNKNOWN",
        "NOT_APPLICABLE",
        "PASS",
        "DONE",
        "READY",
        "TEST",
        "FAKE",
    ];
    !value.is_empty()
        && value.len() <= 128
        && !GENERIC.contains(&value)
        && !secret_like(value)
        && value
            .bytes()
            .next()
            .is_some_and(|byte| byte.is_ascii_alphanumeric())
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'))
}

fn secret_like(value: &str) -> bool {
    let lowercase = value.to_ascii_lowercase();
    lowercase.starts_with("sk-")
        || lowercase.starts_with("ghp_")
        || lowercase.starts_with("github_pat_")
        || lowercase.starts_with("xoxb-")
        || lowercase.contains("password")
        || lowercase.contains("secret")
        || lowercase.contains("private_key")
}

fn semantic_version(value: &str) -> bool {
    let parts: Vec<&str> = value.split('.').collect();
    parts.len() == 3
        && parts.iter().all(|part| {
            !part.is_empty()
                && part.bytes().all(|byte| byte.is_ascii_digit())
                && part
                    .parse::<u32>()
                    .is_ok_and(|number| number.to_string() == *part)
        })
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
    if value.is_empty() || value.len() > 256 {
        return false;
    }
    let components: Vec<&str> = value.split('/').collect();
    components.len() <= 16
        && components.iter().all(|component| {
            !component.is_empty()
                && component.chars().count() <= 64
                && component.chars().next().is_some_and(char::is_alphanumeric)
                && component.chars().all(|character| {
                    character.is_alphanumeric() || matches!(character, '.' | '_' | '-')
                })
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

fn validate_candidate(candidate: &Candidate, schema: &str) -> Result<(), RecordError> {
    let candidate_id = candidate.candidate_id.value().map(String::as_str);
    let candidate_hash = candidate.candidate_hash.value().map(String::as_str);
    if (schema != "2.6.0" && (candidate_id.is_none() || candidate_hash.is_none()))
        || (candidate_id.is_none() != candidate_hash.is_none())
    {
        return Err(RecordError::Invalid);
    }
    let empty = candidate.repository.is_empty()
        && candidate.version.is_empty()
        && candidate.commit.is_empty()
        && candidate_id.is_none_or(str::is_empty)
        && candidate_hash.is_none_or(str::is_empty);
    if empty {
        return Ok(());
    }
    let legacy_without_identity = schema == "2.6.0" && candidate_id.is_none();
    let candidate_id = candidate_id.unwrap_or("");
    let candidate_hash = candidate_hash.unwrap_or("");
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
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        || (!legacy_without_identity
            && (candidate_id.is_empty()
                || !safe_ref(candidate_id)
                || candidate_hash.is_empty()
                || !safe_sha256(candidate_hash)))
    {
        return Err(RecordError::Invalid);
    }
    Ok(())
}

fn validate_security_identity(value: &VulnerabilityClosureState) -> Result<(), RecordError> {
    validate_identity_value(&value.candidate_id, false)?;
    validate_hash_value(&value.candidate_hash)?;
    validate_identity_value(&value.current_receipt_id, false)?;
    validate_identity_value(&value.current_receipt_reference, true)?;
    validate_identity_value(&value.superseded_receipt_id, false)?;
    validate_identity_value(&value.superseded_receipt_reference, true)?;
    validate_identity_value(&value.superseded_candidate_id, false)?;
    validate_hash_value(&value.superseded_candidate_hash)
}

fn validate_post_security_identity(
    value: &PostSecurityOwnerAcceptanceState,
) -> Result<(), RecordError> {
    validate_identity_value(&value.candidate_id, false)?;
    validate_hash_value(&value.candidate_hash)?;
    validate_identity_value(&value.current_acceptance_id, false)?;
    validate_identity_value(&value.current_acceptance_reference, true)?;
    validate_identity_value(&value.vulnerability_closure_receipt_id, false)?;
    validate_identity_value(&value.vulnerability_closure_receipt_reference, true)?;
    validate_identity_value(&value.superseded_acceptance_id, false)?;
    validate_identity_value(&value.superseded_acceptance_reference, true)?;
    validate_identity_value(&value.superseded_candidate_id, false)?;
    validate_hash_value(&value.superseded_candidate_hash)
}

fn validate_identity_value(value: &str, reference: bool) -> Result<(), RecordError> {
    if value == "NOT_APPLICABLE"
        || (!reference && safe_ref(value))
        || (reference && safe_ref(value))
    {
        Ok(())
    } else {
        Err(RecordError::Invalid)
    }
}

fn validate_hash_value(value: &str) -> Result<(), RecordError> {
    if value == "NOT_APPLICABLE" || safe_sha256(value) {
        Ok(())
    } else {
        Err(RecordError::Invalid)
    }
}

fn safe_sha256(value: &str) -> bool {
    value.strip_prefix("sha256:").is_some_and(|digest| {
        digest.len() == 64
            && digest
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    })
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
