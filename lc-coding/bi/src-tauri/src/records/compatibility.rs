use std::collections::BTreeSet;

use serde::Deserialize;

use super::{RecordError, strict_json};

const ASSET_SCHEMA: &str = "LCCODING_BI_COMPATIBILITY_V1";
const NORMALIZATION_MAPPING: [&str; 7] = [
    "worker_checker_wake",
    "supervisor_wait",
    "heartbeat",
    "no_subagents",
    "progress",
    "cell_capacity",
    "pin_policy",
];
const EMBEDDED_ASSET: &str = include_str!("../../../release/loop-contract-identities.json");

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ExecutionMethodIdentity {
    pub version: String,
    pub compatibility_status: String,
    pub minimum_bi_version: String,
    pub adapter_schema_kind: String,
    pub normalization_mapping: Vec<String>,
    pub candidate_commit: String,
    pub manifest_sha256: String,
    pub schema_sha256: String,
    pub template_sha256: String,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct PhaseSteps {
    #[serde(rename = "INITIAL")]
    initial: Vec<String>,
    #[serde(rename = "PRODUCT_FORMATION")]
    product_formation: Vec<String>,
    #[serde(rename = "ENGINEERING_RUNS")]
    engineering_runs: Vec<String>,
    #[serde(rename = "DELIVERY_PREPARATION")]
    delivery_preparation: Vec<String>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct StatusAdapter {
    status_schema_version: String,
    compatibility_status: String,
    minimum_bi_version: String,
    phase_steps: PhaseSteps,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct StatusAdapters {
    #[serde(rename = "2.6.0")]
    legacy_260: StatusAdapter,
    #[serde(rename = "2.7.0")]
    current_270: StatusAdapter,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ExecutionMethods {
    slk: ExecutionMethodIdentity,
    clk: ExecutionMethodIdentity,
    glk: ExecutionMethodIdentity,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompatibilityAsset {
    asset_schema: String,
    status_adapters: StatusAdapters,
    execution_methods: ExecutionMethods,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct StatusPhaseSteps {
    pub phase_id: &'static str,
    pub step_ids: Vec<String>,
}

impl CompatibilityAsset {
    pub fn execution_method(&self, method_id: &str) -> Option<&ExecutionMethodIdentity> {
        match method_id {
            "slk" => Some(&self.execution_methods.slk),
            "clk" => Some(&self.execution_methods.clk),
            "glk" => Some(&self.execution_methods.glk),
            _ => None,
        }
    }

    pub fn status_phase_steps(&self, status_schema_version: &str) -> Option<Vec<StatusPhaseSteps>> {
        let steps = match status_schema_version {
            "2.6.0" => &self.status_adapters.legacy_260.phase_steps,
            "2.7.0" => &self.status_adapters.current_270.phase_steps,
            _ => return None,
        };
        Some(vec![
            StatusPhaseSteps {
                phase_id: "INITIAL",
                step_ids: steps.initial.clone(),
            },
            StatusPhaseSteps {
                phase_id: "PRODUCT_FORMATION",
                step_ids: steps.product_formation.clone(),
            },
            StatusPhaseSteps {
                phase_id: "ENGINEERING_RUNS",
                step_ids: steps.engineering_runs.clone(),
            },
            StatusPhaseSteps {
                phase_id: "DELIVERY_PREPARATION",
                step_ids: steps.delivery_preparation.clone(),
            },
        ])
    }
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

fn lowercase_hex(value: &str, length: usize) -> bool {
    value.len() == length
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn machine_id(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 96
        && value
            .bytes()
            .all(|byte| byte.is_ascii_uppercase() || byte.is_ascii_digit() || byte == b'_')
}

fn phase_step_set(adapter: &StatusAdapter) -> Option<BTreeSet<&str>> {
    let phases = [
        &adapter.phase_steps.initial,
        &adapter.phase_steps.product_formation,
        &adapter.phase_steps.engineering_runs,
        &adapter.phase_steps.delivery_preparation,
    ];
    if phases.iter().any(|phase| phase.is_empty()) {
        return None;
    }
    let flattened: Vec<&str> = phases
        .iter()
        .flat_map(|phase| phase.iter().map(String::as_str))
        .collect();
    let unique: BTreeSet<&str> = flattened.iter().copied().collect();
    (flattened.len() == 21
        && unique.len() == 21
        && flattened
            .iter()
            .all(|step| machine_id(step) && canonical_status_step(step)))
    .then_some(unique)
}

fn canonical_status_step(step: &str) -> bool {
    matches!(
        step,
        "PROPOSAL_READINESS"
            | "PROJECT_INITIALIZATION"
            | "INITIAL_READY"
            | "CALABASH_DRAFT"
            | "SIMULATION_WORLD_FOUNDATION"
            | "WORKFLOW_CAPABILITY_END"
            | "UI_PRODUCT_SURFACE_END"
            | "CALABASH_UPGRADE_READY"
            | "MANDATORY_CALABASH_UPGRADE"
            | "PRODUCT_BASELINE"
            | "FEATURE_SLICE_EXECUTION_COVERAGE"
            | "UI_LOCKED_INTEGRATION_BASELINE"
            | "LOOP_RUN_D0_D3"
            | "LOOP_OWNER_ACCEPTANCE"
            | "ALL_REQUIRED_RUNS_ACCEPTED"
            | "CENTRALIZED_VULNERABILITY_AUDIT"
            | "SECURITY_REMEDIATION"
            | "SECURITY_REAUDIT_VULNERABILITY_CLOSURE"
            | "POST_SECURITY_OWNER_ACCEPTANCE"
            | "DELIVERY_METHOD_QA"
            | "DELIVERY_PACKAGE_GUARD_READY"
    )
}

fn validate_status_adapters(adapters: &StatusAdapters) -> bool {
    let legacy = &adapters.legacy_260;
    let current = &adapters.current_270;
    legacy.status_schema_version == "2.6.0"
        && legacy.compatibility_status == "SUPPORTED_LEGACY"
        && legacy.minimum_bi_version == "2.6.0"
        && current.status_schema_version == "2.7.0"
        && current.compatibility_status == "CURRENT"
        && current.minimum_bi_version == "2.7.0"
        && phase_step_set(legacy).is_some_and(|steps| {
            phase_step_set(current).is_some_and(|current_steps| steps == current_steps)
        })
        && legacy.phase_steps.initial == current.phase_steps.initial
        && legacy.phase_steps.delivery_preparation == current.phase_steps.delivery_preparation
        && legacy.phase_steps.initial.len() == 3
        && legacy.phase_steps.product_formation.len() == 5
        && legacy.phase_steps.engineering_runs.len() == 7
        && legacy.phase_steps.delivery_preparation.len() == 6
        && current.phase_steps.product_formation.len() == 7
        && current.phase_steps.engineering_runs.len() == 5
        && current.phase_steps.product_formation[..5] == legacy.phase_steps.product_formation
        && current.phase_steps.product_formation[5..] == legacy.phase_steps.engineering_runs[..2]
        && current.phase_steps.engineering_runs == legacy.phase_steps.engineering_runs[2..]
}

fn validate_method(method_id: &str, method: &ExecutionMethodIdentity) -> bool {
    let expected_kind = match method_id {
        "slk" => "SLK_RUN_RUNTIME_INDEX",
        "clk" => "CLK_RUN_CONTROL_TRACE",
        "glk" => "GLK_RUN_PACKAGE_INDEX",
        _ => return false,
    };
    semantic_version(&method.version)
        && method.compatibility_status == "CURRENT"
        && method.minimum_bi_version == "2.6.0"
        && method.adapter_schema_kind == expected_kind
        && method
            .normalization_mapping
            .iter()
            .map(String::as_str)
            .eq(NORMALIZATION_MAPPING)
        && lowercase_hex(&method.candidate_commit, 40)
        && lowercase_hex(&method.manifest_sha256, 64)
        && lowercase_hex(&method.schema_sha256, 64)
        && lowercase_hex(&method.template_sha256, 64)
}

pub fn parse_compatibility_asset(body: &str) -> Result<CompatibilityAsset, RecordError> {
    let asset: CompatibilityAsset = strict_json::parse(body)?;
    if asset.asset_schema != ASSET_SCHEMA
        || !validate_status_adapters(&asset.status_adapters)
        || !validate_method("slk", &asset.execution_methods.slk)
        || !validate_method("clk", &asset.execution_methods.clk)
        || !validate_method("glk", &asset.execution_methods.glk)
    {
        return Err(RecordError::Invalid);
    }
    Ok(asset)
}

pub fn embedded_compatibility_asset() -> Result<CompatibilityAsset, RecordError> {
    parse_compatibility_asset(EMBEDDED_ASSET)
}
