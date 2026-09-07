use std::collections::BTreeSet;

use serde::Deserialize;

use super::{RecordError, strict_json};

const ASSET_SCHEMA_V1: &str = "LCCODING_BI_COMPATIBILITY_V1";
const ASSET_SCHEMA_V2: &str = "LCCODING_BI_COMPATIBILITY_V2";
const ASSET_SCHEMA_V3: &str = "LCCODING_BI_COMPATIBILITY_V3";
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
    engineering_runs: Option<Vec<String>>,
    #[serde(rename = "REAL_PRODUCT_INTEGRATION")]
    real_product_integration: Option<Vec<String>>,
    #[serde(rename = "REAL_USER_JOURNEY_ACCEPTANCE")]
    real_user_journey_acceptance: Option<Vec<String>>,
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
    adapter_270: StatusAdapter,
    #[serde(rename = "2.8.0")]
    adapter_280: Option<StatusAdapter>,
    #[serde(rename = "3.0.0")]
    adapter_300: Option<StatusAdapter>,
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
        let (steps, integration_phase_id) = match status_schema_version {
            "2.6.0" => (
                &self.status_adapters.legacy_260.phase_steps,
                "ENGINEERING_RUNS",
            ),
            "2.7.0" => (
                &self.status_adapters.adapter_270.phase_steps,
                "ENGINEERING_RUNS",
            ),
            "2.8.0" => (
                &self.status_adapters.adapter_280.as_ref()?.phase_steps,
                "REAL_PRODUCT_INTEGRATION",
            ),
            "3.0.0" => (
                &self.status_adapters.adapter_300.as_ref()?.phase_steps,
                "REAL_PRODUCT_INTEGRATION",
            ),
            _ => return None,
        };
        let integration_steps = match integration_phase_id {
            "ENGINEERING_RUNS" => steps.engineering_runs.as_ref()?,
            "REAL_PRODUCT_INTEGRATION" => steps.real_product_integration.as_ref()?,
            _ => return None,
        };
        let mut phases = vec![
            StatusPhaseSteps {
                phase_id: "INITIAL",
                step_ids: steps.initial.clone(),
            },
            StatusPhaseSteps {
                phase_id: "PRODUCT_FORMATION",
                step_ids: steps.product_formation.clone(),
            },
            StatusPhaseSteps {
                phase_id: integration_phase_id,
                step_ids: integration_steps.clone(),
            },
        ];
        if status_schema_version == "3.0.0" {
            phases.push(StatusPhaseSteps {
                phase_id: "REAL_USER_JOURNEY_ACCEPTANCE",
                step_ids: steps.real_user_journey_acceptance.as_ref()?.clone(),
            });
        }
        phases.push(StatusPhaseSteps {
            phase_id: "DELIVERY_PREPARATION",
            step_ids: steps.delivery_preparation.clone(),
        });
        Some(phases)
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

fn phase_step_set<'a>(
    adapter: &'a StatusAdapter,
    integration_phase_id: &str,
    include_journey: bool,
) -> Option<BTreeSet<&'a str>> {
    let integration_steps = match integration_phase_id {
        "ENGINEERING_RUNS" if adapter.phase_steps.real_product_integration.is_none() => {
            adapter.phase_steps.engineering_runs.as_ref()?
        }
        "REAL_PRODUCT_INTEGRATION" if adapter.phase_steps.engineering_runs.is_none() => {
            adapter.phase_steps.real_product_integration.as_ref()?
        }
        _ => return None,
    };
    let mut phases = vec![
        &adapter.phase_steps.initial,
        &adapter.phase_steps.product_formation,
        integration_steps,
    ];
    if include_journey {
        phases.push(adapter.phase_steps.real_user_journey_acceptance.as_ref()?);
    } else if adapter.phase_steps.real_user_journey_acceptance.is_some() {
        return None;
    }
    phases.push(&adapter.phase_steps.delivery_preparation);
    if phases.iter().any(|phase| phase.is_empty()) {
        return None;
    }
    let flattened: Vec<&str> = phases
        .iter()
        .flat_map(|phase| phase.iter().map(String::as_str))
        .collect();
    let unique: BTreeSet<&str> = flattened.iter().copied().collect();
    let expected: Vec<&str> = if include_journey {
        CANONICAL_300_STEPS.to_vec()
    } else {
        CANONICAL_280_STEPS.to_vec()
    };
    (flattened == expected
        && unique.len() == expected.len()
        && flattened.iter().all(|step| machine_id(step)))
    .then_some(unique)
}

const CANONICAL_280_STEPS: [&str; 21] = [
    "PROPOSAL_READINESS", "PROJECT_INITIALIZATION", "INITIAL_READY",
    "CALABASH_DRAFT", "SIMULATION_WORLD_FOUNDATION", "WORKFLOW_CAPABILITY_END",
    "UI_PRODUCT_SURFACE_END", "CALABASH_UPGRADE_READY", "MANDATORY_CALABASH_UPGRADE",
    "PRODUCT_BASELINE", "FEATURE_SLICE_EXECUTION_COVERAGE",
    "UI_LOCKED_INTEGRATION_BASELINE", "LOOP_RUN_D0_D3", "LOOP_OWNER_ACCEPTANCE",
    "ALL_REQUIRED_RUNS_ACCEPTED", "CENTRALIZED_VULNERABILITY_AUDIT",
    "SECURITY_REMEDIATION", "SECURITY_REAUDIT_VULNERABILITY_CLOSURE",
    "POST_SECURITY_OWNER_ACCEPTANCE", "DELIVERY_METHOD_QA",
    "DELIVERY_PACKAGE_GUARD_READY",
];
const CANONICAL_300_STEPS: [&str; 26] = [
    "PROPOSAL_READINESS", "PROJECT_INITIALIZATION", "INITIAL_READY",
    "CALABASH_DRAFT", "SIMULATION_WORLD_FOUNDATION", "WORKFLOW_CAPABILITY_END",
    "UI_PRODUCT_SURFACE_END", "CALABASH_UPGRADE_READY", "MANDATORY_CALABASH_UPGRADE",
    "PRODUCT_BASELINE", "FEATURE_SLICE_EXECUTION_COVERAGE",
    "UI_LOCKED_INTEGRATION_BASELINE", "LOOP_RUN_D0_D3", "LOOP_OWNER_ACCEPTANCE",
    "ALL_REQUIRED_RUNS_ACCEPTED", "JOURNEY_COVERAGE_READY",
    "ACCEPTANCE_ENVIRONMENT_READY", "REAL_USER_JOURNEY_ROUND",
    "JOURNEY_DEFECT_CLOSURE", "REAL_USER_JOURNEY_OWNER_ACCEPTANCE",
    "CENTRALIZED_VULNERABILITY_AUDIT", "SECURITY_REMEDIATION",
    "SECURITY_REAUDIT_VULNERABILITY_CLOSURE", "POST_SECURITY_OWNER_ACCEPTANCE",
    "DELIVERY_METHOD_QA", "DELIVERY_PACKAGE_GUARD_READY",
];

fn validate_status_adapters(asset_schema: &str, adapters: &StatusAdapters) -> bool {
    let legacy = &adapters.legacy_260;
    let adapter_270 = &adapters.adapter_270;
    let base_valid = legacy.status_schema_version == "2.6.0"
        && legacy.compatibility_status == "SUPPORTED_LEGACY"
        && legacy.minimum_bi_version == "2.6.0"
        && adapter_270.status_schema_version == "2.7.0"
        && adapter_270.minimum_bi_version == "2.7.0"
        && phase_step_set(legacy, "ENGINEERING_RUNS", false).is_some_and(|steps| {
            phase_step_set(adapter_270, "ENGINEERING_RUNS", false)
                .is_some_and(|adapter_steps| steps == adapter_steps)
        })
        && legacy.phase_steps.initial == adapter_270.phase_steps.initial
        && legacy.phase_steps.delivery_preparation == adapter_270.phase_steps.delivery_preparation
        && legacy.phase_steps.initial.len() == 3
        && legacy.phase_steps.product_formation.len() == 5
        && legacy
            .phase_steps
            .engineering_runs
            .as_ref()
            .is_some_and(|steps| steps.len() == 7)
        && legacy.phase_steps.delivery_preparation.len() == 6
        && adapter_270.phase_steps.product_formation.len() == 7
        && adapter_270
            .phase_steps
            .engineering_runs
            .as_ref()
            .is_some_and(|steps| steps.len() == 5)
        && adapter_270.phase_steps.product_formation[..5] == legacy.phase_steps.product_formation
        && adapter_270.phase_steps.product_formation[5..]
            == legacy.phase_steps.engineering_runs.as_ref().unwrap()[..2]
        && adapter_270.phase_steps.engineering_runs.as_ref().unwrap()[..]
            == legacy.phase_steps.engineering_runs.as_ref().unwrap()[2..];
    if !base_valid {
        return false;
    }
    match asset_schema {
        ASSET_SCHEMA_V1 => {
            adapter_270.compatibility_status == "CURRENT"
                && adapters.adapter_280.is_none()
                && adapters.adapter_300.is_none()
        }
        ASSET_SCHEMA_V2 => {
            adapter_270.compatibility_status == "SUPPORTED_LEGACY"
                && adapters.adapter_280.as_ref().is_some_and(|adapter_280| {
                    adapter_280.status_schema_version == "2.8.0"
                        && adapter_280.compatibility_status == "CURRENT"
                        && adapter_280.minimum_bi_version == "2.8.0"
                        && phase_step_set(adapter_280, "REAL_PRODUCT_INTEGRATION", false).is_some_and(
                            |adapter_280_steps| {
                                phase_step_set(adapter_270, "ENGINEERING_RUNS", false).is_some_and(
                                    |adapter_270_steps| adapter_280_steps == adapter_270_steps,
                                )
                            },
                        )
                        && adapter_280.phase_steps.initial == adapter_270.phase_steps.initial
                        && adapter_280.phase_steps.product_formation
                            == adapter_270.phase_steps.product_formation
                        && adapter_280.phase_steps.real_product_integration.as_ref()
                            == adapter_270.phase_steps.engineering_runs.as_ref()
                        && adapter_280.phase_steps.delivery_preparation
                            == adapter_270.phase_steps.delivery_preparation
                        && adapter_280.phase_steps.initial.len() == 3
                        && adapter_280.phase_steps.product_formation.len() == 7
                        && adapter_280
                            .phase_steps
                            .real_product_integration
                            .as_ref()
                            .is_some_and(|steps| steps.len() == 5)
                        && adapter_280.phase_steps.delivery_preparation.len() == 6
                })
                && adapters.adapter_300.is_none()
        }
        ASSET_SCHEMA_V3 => {
            adapter_270.compatibility_status == "SUPPORTED_LEGACY"
                && adapters.adapter_280.as_ref().is_some_and(|adapter_280| {
                    adapter_280.status_schema_version == "2.8.0"
                        && adapter_280.compatibility_status == "SUPPORTED_LEGACY"
                        && adapter_280.minimum_bi_version == "2.8.0"
                        && phase_step_set(adapter_280, "REAL_PRODUCT_INTEGRATION", false).is_some()
                        && adapters.adapter_300.as_ref().is_some_and(|adapter_300| {
                            adapter_300.status_schema_version == "3.0.0"
                                && adapter_300.compatibility_status == "CURRENT"
                                && adapter_300.minimum_bi_version == "3.0.0"
                                && phase_step_set(adapter_300, "REAL_PRODUCT_INTEGRATION", true).is_some()
                                && adapter_300.phase_steps.initial == adapter_280.phase_steps.initial
                                && adapter_300.phase_steps.product_formation == adapter_280.phase_steps.product_formation
                                && adapter_300.phase_steps.real_product_integration == adapter_280.phase_steps.real_product_integration
                                && adapter_300.phase_steps.delivery_preparation == adapter_280.phase_steps.delivery_preparation
                                && adapter_300.phase_steps.real_user_journey_acceptance.as_ref().is_some_and(|steps| steps.len() == 5)
                        })
                })
        }
        _ => false,
    }
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
    if !validate_status_adapters(&asset.asset_schema, &asset.status_adapters)
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
