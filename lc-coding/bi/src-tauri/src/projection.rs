use std::collections::{HashMap, HashSet};
use std::fmt;
use std::path::{Path, PathBuf};

use crate::git_reader::GitProject;
use crate::input::{ProjectRecord, read_optional_scoped_record, read_project_record};
use crate::records::compatibility::embedded_compatibility_asset;
use crate::records::loops::{
    GlkArtifact, GovernanceStatus, GovernanceSummary, glk_artifact_refs, parse_clk_governance,
    parse_glk_governance, parse_slk_governance,
};
use crate::records::manifest::CanonicalManifest;
use crate::records::manifest::parse_manifest;
use crate::records::maps::{
    Classification, HandoffRow, ProductBaselineHandoff, SimulationMap, SubtreeType, UiMap,
    WorkflowMap, parse_handoff, parse_simulation_map, parse_ui_map, parse_workflow_map,
};
use crate::records::status::{NormalizedState, StatusRecord, normalize_state, parse_status};
use crate::snapshot::{
    PhaseView, ReportRow, ReportView, Reports, RowValue, Snapshot, StepView, ViewState,
};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ProjectionError {
    Inconsistent,
}

impl ProjectionError {
    pub const fn code(self) -> &'static str {
        "BI_RECORD_INCONSISTENT"
    }
}

impl fmt::Display for ProjectionError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.code())
    }
}

impl std::error::Error for ProjectionError {}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ProjectLoadError {
    code: &'static str,
}

impl ProjectLoadError {
    pub const fn code(self) -> &'static str {
        self.code
    }
}

impl fmt::Display for ProjectLoadError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.code)
    }
}

impl std::error::Error for ProjectLoadError {}

pub fn load_project_snapshot(root: &Path) -> Result<Snapshot, ProjectLoadError> {
    let repository =
        GitProject::open(root).map_err(|error| ProjectLoadError { code: error.code() })?;
    let status_text = read_project_record(root, ProjectRecord::Status)
        .map_err(|error| ProjectLoadError { code: error.code() })?
        .ok_or(ProjectLoadError {
            code: "BI_RECORD_INVALID",
        })?;
    let manifest_text = read_project_record(root, ProjectRecord::Manifest)
        .map_err(|error| ProjectLoadError { code: error.code() })?;
    let workflow_text = read_project_record(root, ProjectRecord::WorkflowMap)
        .map_err(|error| ProjectLoadError { code: error.code() })?;
    let ui_text = read_project_record(root, ProjectRecord::UiMap)
        .map_err(|error| ProjectLoadError { code: error.code() })?;
    let simulation_text = read_project_record(root, ProjectRecord::SimulationWorld)
        .map_err(|error| ProjectLoadError { code: error.code() })?;
    let handoff_text = read_project_record(root, ProjectRecord::ProductBaselineHandoff)
        .map_err(|error| ProjectLoadError { code: error.code() })?;
    let status =
        parse_status(&status_text).map_err(|error| ProjectLoadError { code: error.code() })?;
    let manifest = manifest_text
        .as_deref()
        .map(parse_manifest)
        .transpose()
        .map_err(|error| ProjectLoadError { code: error.code() })?;
    let workflow = workflow_text
        .as_deref()
        .map(parse_workflow_map)
        .transpose()
        .map_err(|error| ProjectLoadError { code: error.code() })?;
    let ui = ui_text
        .as_deref()
        .map(parse_ui_map)
        .transpose()
        .map_err(|error| ProjectLoadError { code: error.code() })?;
    let simulation = simulation_text
        .as_deref()
        .map(parse_simulation_map)
        .transpose()
        .map_err(|error| ProjectLoadError { code: error.code() })?;
    let handoff = handoff_text
        .as_deref()
        .map(parse_handoff)
        .transpose()
        .map_err(|error| ProjectLoadError { code: error.code() })?;

    if !status.canonical_candidate.commit.is_empty() {
        repository
            .read_blob_at(
                &status.canonical_candidate.commit,
                &PathBuf::from(".lccoding/status.json"),
            )
            .map_err(|error| ProjectLoadError { code: error.code() })?;
    }
    let mut snapshot = snapshot_from_status(&status, manifest.as_ref())
        .map_err(|error| ProjectLoadError { code: error.code() })?;
    apply_product_records(
        &repository,
        &status,
        workflow.as_ref(),
        ui.as_ref(),
        simulation.as_ref(),
        handoff.as_ref(),
        &mut snapshot,
    )?;
    if let Some(summary) = load_loop_governance(root, &status, manifest.as_ref())? {
        apply_loop_summary(&summary, &mut snapshot.reports.loop_governance);
    }
    Ok(snapshot)
}

pub fn load_loop_governance(
    root: &Path,
    status: &StatusRecord,
    manifest: Option<&CanonicalManifest>,
) -> Result<Option<GovernanceSummary>, ProjectLoadError> {
    if status.active_runs.is_empty() {
        return Ok(None);
    }
    let manifest = manifest.ok_or(ProjectLoadError {
        code: "BI_METHOD_VERSION_UNSUPPORTED",
    })?;
    let compatibility =
        embedded_compatibility_asset().map_err(|error| ProjectLoadError { code: error.code() })?;
    let mut summaries = Vec::with_capacity(status.active_runs.len());
    for run_ref in &status.active_runs {
        let scope = Path::new(run_ref);
        let slk = read_optional_scoped_record(root, scope, Path::new("RUN_RUNTIME_INDEX.yaml"))
            .map_err(|error| ProjectLoadError { code: error.code() })?;
        let clk = read_optional_scoped_record(root, scope, Path::new("CLK_RUN_CONTROL_TRACE.yaml"))
            .map_err(|error| ProjectLoadError { code: error.code() })?;
        let glk = read_optional_scoped_record(root, scope, Path::new("RUN_PACKAGE_INDEX.yaml"))
            .map_err(|error| ProjectLoadError { code: error.code() })?;
        if usize::from(slk.is_some()) + usize::from(clk.is_some()) + usize::from(glk.is_some()) != 1
        {
            return Err(ProjectLoadError {
                code: "BI_RECORD_INCONSISTENT",
            });
        }
        let summary = if let Some(body) = slk {
            let identity = compatibility
                .execution_method("slk")
                .ok_or(ProjectLoadError {
                    code: "BI_RECORD_INVALID",
                })?;
            require_method_identity(
                &manifest.slk.version,
                &manifest.slk.hash,
                &identity.version,
                &identity.manifest_sha256,
            )?;
            parse_slk_governance(&body).map_err(|error| ProjectLoadError { code: error.code() })?
        } else if let Some(body) = clk {
            let identity = compatibility
                .execution_method("clk")
                .ok_or(ProjectLoadError {
                    code: "BI_RECORD_INVALID",
                })?;
            require_method_identity(
                &manifest.clk.version,
                &manifest.clk.hash,
                &identity.version,
                &identity.manifest_sha256,
            )?;
            parse_clk_governance(&body).map_err(|error| ProjectLoadError { code: error.code() })?
        } else {
            let body = glk.expect("exactly one loop index");
            let identity = compatibility
                .execution_method("glk")
                .ok_or(ProjectLoadError {
                    code: "BI_RECORD_INVALID",
                })?;
            require_method_identity(
                &manifest.glk.version,
                &manifest.glk.hash,
                &identity.version,
                &identity.manifest_sha256,
            )?;
            let references = glk_artifact_refs(&body)
                .map_err(|error| ProjectLoadError { code: error.code() })?;
            let mut owned = Vec::with_capacity(references.len());
            for reference in references {
                let artifact = read_optional_scoped_record(root, scope, Path::new(&reference.path))
                    .map_err(|error| ProjectLoadError { code: error.code() })?
                    .ok_or(ProjectLoadError {
                        code: "BI_RECORD_INCONSISTENT",
                    })?;
                owned.push((reference.path, reference.artifact_type, artifact));
            }
            let artifacts: Vec<GlkArtifact<'_>> = owned
                .iter()
                .map(|(path, artifact_type, body)| GlkArtifact {
                    path,
                    artifact_type,
                    body,
                })
                .collect();
            parse_glk_governance(&body, &artifacts)
                .map_err(|error| ProjectLoadError { code: error.code() })?
        };
        summaries.push(summary);
    }
    aggregate_governance(&summaries).map(Some)
}

fn require_method_identity(
    actual_version: &str,
    actual_hash: &str,
    expected_version: &str,
    expected_hash: &str,
) -> Result<(), ProjectLoadError> {
    if actual_version != expected_version
        || actual_hash.strip_prefix("sha256:").unwrap_or(actual_hash) != expected_hash
    {
        return Err(ProjectLoadError {
            code: "BI_METHOD_VERSION_UNSUPPORTED",
        });
    }
    Ok(())
}

fn aggregate_governance(
    summaries: &[GovernanceSummary],
) -> Result<GovernanceSummary, ProjectLoadError> {
    let first = summaries.first().ok_or_else(inconsistent)?;
    let mut metrics = first.metrics;
    for summary in &summaries[1..] {
        for (target, current) in metrics.iter_mut().zip(summary.metrics) {
            target.status = worse_status(target.status, current.status);
            match (
                target.completed,
                target.total,
                current.completed,
                current.total,
            ) {
                (Some(left_done), Some(left_total), Some(right_done), Some(right_total)) => {
                    target.completed = left_done.checked_add(right_done);
                    target.total = left_total.checked_add(right_total);
                    if target.completed.is_none() || target.total.is_none() {
                        return Err(inconsistent());
                    }
                }
                (None, None, None, None) => {}
                _ => {
                    target.completed = None;
                    target.total = None;
                }
            }
            if target.interval_minutes != current.interval_minutes {
                target.interval_minutes = None;
            }
        }
    }
    Ok(GovernanceSummary { metrics })
}

fn worse_status(left: GovernanceStatus, right: GovernanceStatus) -> GovernanceStatus {
    let rank = |status| match status {
        GovernanceStatus::Compliant => 0,
        GovernanceStatus::NotRecorded => 1,
        GovernanceStatus::Unknown => 2,
        GovernanceStatus::Active => 3,
        GovernanceStatus::Violation => 4,
    };
    if rank(left) >= rank(right) {
        left
    } else {
        right
    }
}

fn apply_loop_summary(summary: &GovernanceSummary, report: &mut ReportView) {
    const KEYS: [&str; 7] = [
        "row.worker_checker_wake",
        "row.supervisor_wait",
        "row.heartbeat",
        "row.no_subagents",
        "row.progress",
        "row.cell_capacity",
        "row.pin_policy",
    ];
    for (key, metric) in KEYS.into_iter().zip(summary.metrics) {
        let row = report
            .rows
            .iter_mut()
            .find(|row| row.key == key)
            .expect("closed Loop Governance metric key");
        row.value = RowValue::Metric {
            status: match metric.status {
                GovernanceStatus::Compliant => "COMPLIANT",
                GovernanceStatus::Active => "ACTIVE",
                GovernanceStatus::Violation => "VIOLATION",
                GovernanceStatus::Unknown => "UNKNOWN",
                GovernanceStatus::NotRecorded => "NOT_RECORDED",
            },
            completed: metric.completed,
            total: metric.total,
            interval_minutes: metric.interval_minutes,
        };
    }
}

#[derive(Debug)]
struct ExpectedIdentity {
    path: String,
    version: String,
    content_hash: String,
    classification: Option<Classification>,
    api_evidence: Option<String>,
    mcp_evidence: Option<String>,
    primary: bool,
    related_ids: HashSet<String>,
}

fn apply_product_records(
    repository: &GitProject,
    status: &StatusRecord,
    workflow: Option<&WorkflowMap>,
    ui: Option<&UiMap>,
    simulation: Option<&SimulationMap>,
    handoff: Option<&ProductBaselineHandoff>,
    snapshot: &mut Snapshot,
) -> Result<(), ProjectLoadError> {
    if let Some(map) = simulation {
        project_simulation_metrics(map, &mut snapshot.reports.simulation);
    }
    if let Some(map) = workflow {
        project_workflow_metrics(map, &mut snapshot.reports.workflow);
    }
    if let Some(map) = ui {
        project_ui_metrics(map, &mut snapshot.reports.ui);
    }

    let baseline_done = matches!(
        normalize_state(&status.product_baseline),
        Some(NormalizedState::Done)
    );
    if baseline_done
        && (workflow.is_none() || ui.is_none() || simulation.is_none() || handoff.is_none())
    {
        return Err(inconsistent());
    }

    match handoff {
        None => Ok(()),
        Some(value) if value.complete => {
            if !baseline_done {
                return Err(inconsistent());
            }
            let locked = validate_complete_baseline(
                repository,
                workflow.ok_or_else(inconsistent)?,
                ui.ok_or_else(inconsistent)?,
                simulation.ok_or_else(inconsistent)?,
                value,
            )?;
            set_metric(
                &mut snapshot.reports.baseline,
                "row.git_identity",
                "COMPLIANT",
                None,
                None,
            );
            set_metric(
                &mut snapshot.reports.baseline,
                "row.locked_subtree_coverage",
                "COMPLIANT",
                Some(locked),
                Some(locked),
            );
            set_metric(
                &mut snapshot.reports.baseline,
                "row.map_handoff_consistency",
                "COMPLIANT",
                None,
                None,
            );
            set_metric(
                &mut snapshot.reports.baseline,
                "row.owner_confirmed_mainline",
                "COMPLIANT",
                None,
                None,
            );
            Ok(())
        }
        Some(_) if baseline_done => Err(inconsistent()),
        Some(_) => {
            for key in [
                "row.git_identity",
                "row.locked_subtree_coverage",
                "row.map_handoff_consistency",
                "row.owner_confirmed_mainline",
            ] {
                set_metric(&mut snapshot.reports.baseline, key, "ACTIVE", None, None);
            }
            Ok(())
        }
    }
}

fn project_simulation_metrics(map: &SimulationMap, report: &mut ReportView) {
    let total = count(map.rows.len());
    if total == 0 {
        for key in [
            "row.realized_peer_subtrees",
            "row.component_version_coverage",
            "row.primary_mainline",
        ] {
            set_metric(report, key, "UNKNOWN", None, None);
        }
        return;
    }
    let realized = count(
        map.rows
            .iter()
            .filter(|row| matches!(row.foundation_status.as_str(), "REALIZED" | "COMPLETE"))
            .count(),
    );
    let realized_status = if map
        .rows
        .iter()
        .any(|row| row.foundation_status == "BLOCKED")
    {
        "VIOLATION"
    } else if map
        .rows
        .iter()
        .any(|row| row.foundation_status == "UNKNOWN")
    {
        "UNKNOWN"
    } else if realized == total {
        "COMPLIANT"
    } else {
        "ACTIVE"
    };
    set_metric(
        report,
        "row.realized_peer_subtrees",
        realized_status,
        Some(realized),
        Some(total),
    );
    set_metric(
        report,
        "row.component_version_coverage",
        "COMPLIANT",
        Some(total),
        Some(total),
    );
    let primary = map.rows.iter().any(|row| {
        row.primary && matches!(row.foundation_status.as_str(), "REALIZED" | "COMPLETE")
    });
    set_metric(
        report,
        "row.primary_mainline",
        if primary { "COMPLIANT" } else { "VIOLATION" },
        None,
        None,
    );
}

fn project_workflow_metrics(map: &WorkflowMap, report: &mut ReportView) {
    let core_total = count(
        map.rows
            .iter()
            .filter(|row| row.classification == Classification::Core)
            .count(),
    );
    let core_implemented = count(
        map.rows
            .iter()
            .filter(|row| row.classification == Classification::Core && row.implemented)
            .count(),
    );
    set_metric(
        report,
        "row.core_implementation",
        if core_total == 0 {
            "UNKNOWN"
        } else if core_total == core_implemented {
            "COMPLIANT"
        } else {
            "ACTIVE"
        },
        Some(core_implemented),
        Some(core_total),
    );

    let extra_total = count(
        map.rows
            .iter()
            .filter(|row| row.classification == Classification::Extra)
            .count(),
    );
    let extra_implemented = count(
        map.rows
            .iter()
            .filter(|row| row.classification == Classification::Extra && row.implemented)
            .count(),
    );
    set_metric(
        report,
        "row.extra_implemented",
        "COMPLIANT",
        Some(extra_implemented),
        Some(extra_total),
    );
    set_metric(
        report,
        "row.extra_deferred",
        "COMPLIANT",
        Some(extra_total.saturating_sub(extra_implemented)),
        Some(extra_total),
    );

    let implemented = map
        .rows
        .iter()
        .filter(|row| row.implemented)
        .collect::<Vec<_>>();
    let implemented_total = count(implemented.len());
    let api = count(
        implemented
            .iter()
            .filter(|row| row.api_evidence.is_some())
            .count(),
    );
    let mcp = count(
        implemented
            .iter()
            .filter(|row| row.mcp_evidence.is_some())
            .count(),
    );
    set_metric(
        report,
        "row.api_coverage",
        coverage_status(api, implemented_total),
        Some(api),
        Some(implemented_total),
    );
    set_metric(
        report,
        "row.mcp_coverage",
        coverage_status(mcp, implemented_total),
        Some(mcp),
        Some(implemented_total),
    );
    let versions = count(
        implemented
            .iter()
            .filter(|row| row.version.is_some())
            .count(),
    );
    set_metric(
        report,
        "row.component_version_coverage",
        coverage_status(versions, implemented_total),
        Some(versions),
        Some(implemented_total),
    );
    let primary = map
        .rows
        .iter()
        .any(|row| row.primary && row.implemented && row.classification == Classification::Core);
    set_metric(
        report,
        "row.primary_mainline",
        if primary { "COMPLIANT" } else { "VIOLATION" },
        None,
        None,
    );
}

fn project_ui_metrics(map: &UiMap, report: &mut ReportView) {
    let total = count(map.rows.len());
    if total == 0 {
        for key in [
            "row.realized_subtrees",
            "row.component_version_coverage",
            "row.lock_status",
            "row.primary_mainline",
        ] {
            set_metric(report, key, "UNKNOWN", None, None);
        }
        return;
    }
    set_metric(
        report,
        "row.realized_subtrees",
        "COMPLIANT",
        Some(total),
        Some(total),
    );
    set_metric(
        report,
        "row.component_version_coverage",
        "COMPLIANT",
        Some(total),
        Some(total),
    );
    let locked = count(
        map.rows
            .iter()
            .filter(|row| row.lock_status == "LOCKED")
            .count(),
    );
    let lock_status = if map.rows.iter().any(|row| row.lock_status == "BLOCKED") {
        "VIOLATION"
    } else if map.rows.iter().any(|row| row.lock_status == "UNKNOWN") {
        "UNKNOWN"
    } else if locked == total {
        "COMPLIANT"
    } else {
        "ACTIVE"
    };
    set_metric(
        report,
        "row.lock_status",
        lock_status,
        Some(locked),
        Some(total),
    );
    set_metric(
        report,
        "row.primary_mainline",
        if map.rows.iter().any(|row| row.primary) {
            "COMPLIANT"
        } else {
            "VIOLATION"
        },
        None,
        None,
    );
}

fn validate_complete_baseline(
    repository: &GitProject,
    workflow: &WorkflowMap,
    ui: &UiMap,
    simulation: &SimulationMap,
    handoff: &ProductBaselineHandoff,
) -> Result<u32, ProjectLoadError> {
    if handoff.repository_identity.is_empty()
        || workflow.mainline_id != handoff.mainline_id
        || ui.mainline_id != handoff.mainline_id
        || simulation.mainline_id != handoff.mainline_id
        || !handoff.owner_confirmation.starts_with("OWNER_CONFIRMED:")
    {
        return Err(inconsistent());
    }
    if workflow.rows.iter().any(|row| {
        (row.classification == Classification::Core && !row.implemented)
            || (row.implemented && (row.api_evidence.is_none() || row.mcp_evidence.is_none()))
    }) || ui.rows.iter().any(|row| row.lock_status != "LOCKED")
        || simulation
            .rows
            .iter()
            .any(|row| !matches!(row.foundation_status.as_str(), "REALIZED" | "COMPLETE"))
    {
        return Err(inconsistent());
    }

    let mut expected = HashMap::new();
    let mut global_ids = HashSet::new();
    for row in workflow.rows.iter().filter(|row| row.implemented) {
        if !global_ids.insert(row.id.clone()) {
            return Err(inconsistent());
        }
        let mut related_ids = row.ui_refs.iter().cloned().collect::<HashSet<_>>();
        related_ids.extend(row.simulation_refs.iter().cloned());
        expected.insert(
            (SubtreeType::Workflow, row.id.clone()),
            ExpectedIdentity {
                path: row.path.clone().ok_or_else(inconsistent)?,
                version: row.version.clone().ok_or_else(inconsistent)?,
                content_hash: row.content_hash.clone().ok_or_else(inconsistent)?,
                classification: Some(row.classification),
                api_evidence: row.api_evidence.clone(),
                mcp_evidence: row.mcp_evidence.clone(),
                primary: row.primary,
                related_ids,
            },
        );
    }
    for row in &ui.rows {
        if !global_ids.insert(row.id.clone()) {
            return Err(inconsistent());
        }
        let mut related_ids = row.workflow_refs.iter().cloned().collect::<HashSet<_>>();
        related_ids.extend(row.simulation_refs.iter().cloned());
        expected.insert(
            (SubtreeType::Ui, row.id.clone()),
            ExpectedIdentity {
                path: row.path.clone(),
                version: row.version.clone(),
                content_hash: row.content_hash.clone(),
                classification: None,
                api_evidence: None,
                mcp_evidence: None,
                primary: row.primary,
                related_ids,
            },
        );
    }
    for row in &simulation.rows {
        if !global_ids.insert(row.id.clone()) {
            return Err(inconsistent());
        }
        let mut related_ids = row.workflow_refs.iter().cloned().collect::<HashSet<_>>();
        related_ids.extend(row.ui_refs.iter().cloned());
        expected.insert(
            (SubtreeType::Simulation, row.id.clone()),
            ExpectedIdentity {
                path: row.path.clone(),
                version: row.version.clone(),
                content_hash: row.content_hash.clone(),
                classification: None,
                api_evidence: None,
                mcp_evidence: None,
                primary: row.primary,
                related_ids,
            },
        );
    }
    if expected.is_empty() || expected.len() != handoff.rows.len() {
        return Err(inconsistent());
    }
    for identity in expected.values() {
        if identity
            .related_ids
            .iter()
            .any(|id| !global_ids.contains(id))
        {
            return Err(inconsistent());
        }
    }

    let primary_ui = ui
        .rows
        .iter()
        .filter(|row| row.primary)
        .map(|row| row.id.as_str())
        .collect::<HashSet<_>>();
    let primary_simulation = simulation
        .rows
        .iter()
        .filter(|row| row.primary)
        .map(|row| row.id.as_str())
        .collect::<HashSet<_>>();
    let primary_workflows = workflow
        .rows
        .iter()
        .filter(|row| row.primary && row.implemented && row.classification == Classification::Core)
        .collect::<Vec<_>>();
    if primary_ui.is_empty() || primary_simulation.is_empty() || primary_workflows.is_empty() {
        return Err(inconsistent());
    }
    for row in primary_workflows {
        if !row
            .ui_refs
            .iter()
            .any(|id| primary_ui.contains(id.as_str()))
            || !row
                .simulation_refs
                .iter()
                .any(|id| primary_simulation.contains(id.as_str()))
        {
            return Err(inconsistent());
        }
    }

    for row in &handoff.rows {
        let identity = expected
            .get(&(row.subtree_type, row.id.clone()))
            .ok_or_else(inconsistent)?;
        if !handoff_row_matches(identity, row) {
            return Err(inconsistent());
        }
        let actual_hash = repository
            .subtree_content_hash(&handoff.frozen_commit, Path::new(&row.path))
            .map_err(|error| ProjectLoadError { code: error.code() })?;
        if actual_hash != row.content_hash {
            return Err(inconsistent());
        }
    }
    Ok(count(expected.len()))
}

fn handoff_row_matches(expected: &ExpectedIdentity, actual: &HandoffRow) -> bool {
    expected.path == actual.path
        && expected.version == actual.version
        && expected.content_hash == actual.content_hash
        && expected.classification == actual.classification
        && expected.api_evidence == actual.api_evidence
        && expected.mcp_evidence == actual.mcp_evidence
        && expected.primary == actual.primary
        && expected.related_ids == actual.related_ids.iter().cloned().collect()
}

fn set_metric(
    report: &mut ReportView,
    key: &'static str,
    status: &'static str,
    completed: Option<u32>,
    total: Option<u32>,
) {
    let row = report
        .rows
        .iter_mut()
        .find(|row| row.key == key)
        .expect("closed report metric key");
    row.value = RowValue::Metric {
        status,
        completed,
        total,
        interval_minutes: None,
    };
}

fn coverage_status(completed: u32, total: u32) -> &'static str {
    if total == 0 {
        "UNKNOWN"
    } else if completed == total {
        "COMPLIANT"
    } else {
        "VIOLATION"
    }
}

fn count(value: usize) -> u32 {
    u32::try_from(value).expect("bounded record rows fit u32")
}

const fn inconsistent() -> ProjectLoadError {
    ProjectLoadError {
        code: "BI_RECORD_INCONSISTENT",
    }
}

fn normalized_agent_value(value: &str) -> Result<&'static str, ProjectionError> {
    match value {
        "UNPROVED" => Ok("UNPROVED"),
        "NOT_APPLICABLE" => Ok("NOT_APPLICABLE"),
        "APPLICABLE_EXTRA" => Ok("APPLICABLE_EXTRA"),
        "APPLICABLE_CORE" => Ok("APPLICABLE_CORE"),
        "ACCEPTED" => Ok("ACCEPTED"),
        "VERIFIED" => Ok("VERIFIED"),
        _ => Err(ProjectionError::Inconsistent),
    }
}

fn agent_summary_rows(status: &StatusRecord) -> Result<Vec<ReportRow>, ProjectionError> {
    let integration = status
        .agent_slice_integration()
        .ok_or(ProjectionError::Inconsistent)?;
    let operations = normalized_agent_value(&integration.operations_agent_integration_state)?;
    let applicability = normalized_agent_value(&integration.product_agent_applicability)?;
    let product = normalized_agent_value(&integration.product_agent_integration_state)?;
    let isolation = normalized_agent_value(&integration.dual_agent_isolation_state)?;
    let slice_status = match integration.state.as_str() {
        "UNPROVED" => "UNPROVED",
        "AGENT_SLICES_ACCEPTED" => "ACCEPTED",
        _ => return Err(ProjectionError::Inconsistent),
    };
    Ok(vec![
        ReportRow {
            key: "row.operations_agent_integration",
            value: RowValue::Record { value: operations },
        },
        ReportRow {
            key: "row.product_agent_integration",
            value: RowValue::AgentStatus {
                applicability,
                integration: product,
            },
        },
        ReportRow {
            key: "row.runtime_adapter",
            value: RowValue::SafeIdentity {
                id: integration.runtime_adapter_id.clone(),
                version: integration.runtime_adapter_version.clone(),
            },
        },
        ReportRow {
            key: "row.dual_agent_isolation",
            value: RowValue::Record { value: isolation },
        },
        ReportRow {
            key: "row.product_slice_progress",
            value: RowValue::Metric {
                status: slice_status,
                completed: Some(count(integration.accepted_product_slice_ids.len())),
                total: None,
                interval_minutes: None,
            },
        },
        ReportRow {
            key: "row.operations_slice_progress",
            value: RowValue::Metric {
                status: slice_status,
                completed: Some(count(integration.accepted_operations_slice_ids.len())),
                total: None,
                interval_minutes: None,
            },
        },
    ])
}

pub fn snapshot_from_status(
    status: &StatusRecord,
    manifest: Option<&CanonicalManifest>,
) -> Result<Snapshot, ProjectionError> {
    let manifest_schema = match status.status_schema_version.as_str() {
        "2.6.0" => "2.6.0",
        "2.7.0" => "2.7.0",
        "2.8.0" => "2.8.0",
        _ => return Err(ProjectionError::Inconsistent),
    };
    if manifest.is_some_and(|manifest| manifest.lccoding.version != manifest_schema) {
        return Err(ProjectionError::Inconsistent);
    }

    let aggregate = state(&status.all_required_runs_accepted)?;
    if aggregate != state(&status.phase_gates.all_required_runs_accepted)? {
        return Err(ProjectionError::Inconsistent);
    }
    if aggregate == ViewState::Done
        && (status.loop_owner_acceptances.is_empty()
            || !status.active_runs.is_empty()
            || !status.open_owner_gaps.is_empty())
    {
        return Err(ProjectionError::Inconsistent);
    }

    let feature_slice = if aggregate == ViewState::Done {
        ViewState::Done
    } else if status.active_slice.is_some() {
        ViewState::Active
    } else if status.integration_baseline.is_some()
        || !status.active_runs.is_empty()
        || !status.loop_owner_acceptances.is_empty()
    {
        ViewState::Done
    } else {
        ViewState::Pending
    };
    let integration = if status.integration_baseline.is_some() {
        ViewState::Done
    } else {
        ViewState::Pending
    };
    let run = if aggregate == ViewState::Done {
        ViewState::Done
    } else if aggregate == ViewState::Error {
        ViewState::Error
    } else if !status.active_runs.is_empty() {
        ViewState::Active
    } else if !status.loop_owner_acceptances.is_empty() {
        ViewState::Done
    } else {
        ViewState::Pending
    };
    let acceptance = if aggregate == ViewState::Done {
        if status.loop_owner_acceptances.is_empty() {
            return Err(ProjectionError::Inconsistent);
        }
        ViewState::Done
    } else if aggregate == ViewState::Error {
        ViewState::Error
    } else if !status.loop_owner_acceptances.is_empty() {
        ViewState::Active
    } else {
        ViewState::Pending
    };

    let layouts = embedded_compatibility_asset()
        .map_err(|_| ProjectionError::Inconsistent)?
        .status_phase_steps(&status.status_schema_version)
        .ok_or(ProjectionError::Inconsistent)?;
    let mut phases = layouts
        .iter()
        .map(|layout| {
            let steps = layout
                .step_ids
                .iter()
                .map(|id| {
                    projected_step(
                        status,
                        id,
                        feature_slice,
                        integration,
                        run,
                        acceptance,
                        aggregate,
                    )
                })
                .collect::<Result<Vec<_>, _>>()?;
            Ok(phase(layout.phase_id, steps))
        })
        .collect::<Result<Vec<_>, ProjectionError>>()?;
    apply_phase_truth(status, &mut phases)?;

    let candidate_locked = !status.canonical_candidate.repository.is_empty();
    let calabash_version = manifest.and_then(|manifest| {
        (!manifest.calabash.version.is_empty()).then(|| manifest.calabash.version.clone())
    });
    let mut candidate_rows = vec![
        ReportRow {
            key: "row.identity",
            value: RowValue::Lock {
                value: if candidate_locked {
                    "LOCKED"
                } else {
                    "PENDING"
                },
            },
        },
        ReportRow {
            key: "row.integrity",
            value: RowValue::Record {
                value: if candidate_locked
                    && step_state(&phases, "PROJECT_INITIALIZATION")? == ViewState::Done
                {
                    "RECORDED"
                } else {
                    "PENDING"
                },
            },
        },
    ];
    if status.status_schema_version == "2.8.0" {
        candidate_rows.extend(agent_summary_rows(status)?);
    }
    let reports = Reports {
        proposal: report(
            "proposal",
            step_state(&phases, "PROPOSAL_READINESS")?,
            None,
            vec![
                view_row("row.conclusion", step_state(&phases, "PROPOSAL_READINESS")?),
                view_row("row.initial_gate", step_state(&phases, "INITIAL_READY")?),
            ],
        ),
        candidate: report(
            "candidate",
            step_state(&phases, "PROJECT_INITIALIZATION")?,
            candidate_locked.then(|| status.canonical_candidate.version.clone()),
            candidate_rows,
        ),
        calabash: report(
            "calabash",
            step_state(&phases, "CALABASH_DRAFT")?,
            calabash_version.clone(),
            vec![
                view_row("row.status", step_state(&phases, "CALABASH_DRAFT")?),
                ReportRow {
                    key: "row.version_record",
                    value: RowValue::Record {
                        value: if calabash_version.is_some() {
                            "RECORDED"
                        } else {
                            "NOT_RECORDED"
                        },
                    },
                },
            ],
        ),
        simulation: metric_report(
            "simulation",
            step_state(&phases, "SIMULATION_WORLD_FOUNDATION")?,
            &[
                "row.realized_peer_subtrees",
                "row.component_version_coverage",
                "row.primary_mainline",
            ],
        ),
        workflow: metric_report(
            "workflow",
            step_state(&phases, "WORKFLOW_CAPABILITY_END")?,
            &[
                "row.core_implementation",
                "row.extra_implemented",
                "row.extra_deferred",
                "row.api_coverage",
                "row.mcp_coverage",
                "row.component_version_coverage",
                "row.primary_mainline",
            ],
        ),
        ui: metric_report(
            "ui",
            step_state(&phases, "UI_PRODUCT_SURFACE_END")?,
            &[
                "row.realized_subtrees",
                "row.component_version_coverage",
                "row.lock_status",
                "row.primary_mainline",
            ],
        ),
        baseline: metric_report(
            "baseline",
            step_state(&phases, "PRODUCT_BASELINE")?,
            &[
                "row.git_identity",
                "row.locked_subtree_coverage",
                "row.map_handoff_consistency",
                "row.owner_confirmed_mainline",
            ],
        ),
        loop_governance: metric_report(
            "loop_governance",
            step_state(&phases, "LOOP_RUN_D0_D3")?,
            &[
                "row.worker_checker_wake",
                "row.supervisor_wait",
                "row.heartbeat",
                "row.no_subagents",
                "row.progress",
                "row.cell_capacity",
                "row.pin_policy",
            ],
        ),
    };

    Ok(Snapshot {
        schema: match status.status_schema_version.as_str() {
            "2.6.0" => "LCCoding 2.6.0 derived BI",
            "2.7.0" => "LCCoding 2.7.0 derived BI",
            "2.8.0" => "LCCoding 2.8.0 derived BI",
            _ => return Err(ProjectionError::Inconsistent),
        },
        authoritative: false,
        read_only: true,
        health: "ok",
        project: status.project_id.clone(),
        current_phase: status.current_phase.clone(),
        phases,
        reports,
    })
}

#[allow(clippy::too_many_arguments)]
fn projected_step(
    status: &StatusRecord,
    id: &str,
    feature_slice: ViewState,
    integration: ViewState,
    run: ViewState,
    acceptance: ViewState,
    aggregate: ViewState,
) -> Result<StepView, ProjectionError> {
    let (id, state, report) = match id {
        "PROPOSAL_READINESS" => (
            "PROPOSAL_READINESS",
            state(&status.proposal)?,
            Some("proposal"),
        ),
        "PROJECT_INITIALIZATION" => (
            "PROJECT_INITIALIZATION",
            state(&status.initialization)?,
            Some("candidate"),
        ),
        "INITIAL_READY" => (
            "INITIAL_READY",
            state(&status.phase_gates.initial_ready)?,
            None,
        ),
        "CALABASH_DRAFT" => (
            "CALABASH_DRAFT",
            state(&status.calabash_draft)?,
            Some("calabash"),
        ),
        "SIMULATION_WORLD_FOUNDATION" => (
            "SIMULATION_WORLD_FOUNDATION",
            state(&status.simulation)?,
            Some("simulation"),
        ),
        "WORKFLOW_CAPABILITY_END" => (
            "WORKFLOW_CAPABILITY_END",
            state(&status.workflow)?,
            Some("workflow"),
        ),
        "UI_PRODUCT_SURFACE_END" => ("UI_PRODUCT_SURFACE_END", state(&status.ui)?, Some("ui")),
        "CALABASH_UPGRADE_READY" => (
            "CALABASH_UPGRADE_READY",
            state(&status.phase_gates.calabash_upgrade_ready)?,
            None,
        ),
        "MANDATORY_CALABASH_UPGRADE" => (
            "MANDATORY_CALABASH_UPGRADE",
            state(&status.mandatory_calabash_upgrade)?,
            None,
        ),
        "PRODUCT_BASELINE" => (
            "PRODUCT_BASELINE",
            state(&status.product_baseline)?,
            Some("baseline"),
        ),
        "FEATURE_SLICE_EXECUTION_COVERAGE" => {
            ("FEATURE_SLICE_EXECUTION_COVERAGE", feature_slice, None)
        }
        "UI_LOCKED_INTEGRATION_BASELINE" => ("UI_LOCKED_INTEGRATION_BASELINE", integration, None),
        "LOOP_RUN_D0_D3" => ("LOOP_RUN_D0_D3", run, Some("loop_governance")),
        "LOOP_OWNER_ACCEPTANCE" => ("LOOP_OWNER_ACCEPTANCE", acceptance, None),
        "ALL_REQUIRED_RUNS_ACCEPTED" => ("ALL_REQUIRED_RUNS_ACCEPTED", aggregate, None),
        "CENTRALIZED_VULNERABILITY_AUDIT" => (
            "CENTRALIZED_VULNERABILITY_AUDIT",
            state(&status.centralized_security_audit)?,
            None,
        ),
        "SECURITY_REMEDIATION" => (
            "SECURITY_REMEDIATION",
            state(&status.security_remediation)?,
            None,
        ),
        "SECURITY_REAUDIT_VULNERABILITY_CLOSURE" => (
            "SECURITY_REAUDIT_VULNERABILITY_CLOSURE",
            state(status.vulnerability_closure.state())?,
            None,
        ),
        "POST_SECURITY_OWNER_ACCEPTANCE" => (
            "POST_SECURITY_OWNER_ACCEPTANCE",
            state(status.post_security_owner_acceptance.state())?,
            None,
        ),
        "DELIVERY_METHOD_QA" => (
            "DELIVERY_METHOD_QA",
            state(&status.delivery_method_qa)?,
            None,
        ),
        "DELIVERY_PACKAGE_GUARD_READY" => (
            "DELIVERY_PACKAGE_GUARD_READY",
            state(&status.phase_gates.delivery_ready)?,
            None,
        ),
        _ => return Err(ProjectionError::Inconsistent),
    };
    Ok(step(id, state, report))
}

fn step_state(phases: &[PhaseView], id: &str) -> Result<ViewState, ProjectionError> {
    phases
        .iter()
        .flat_map(|phase| &phase.steps)
        .find(|step| step.id == id)
        .map(|step| step.state)
        .ok_or(ProjectionError::Inconsistent)
}

fn apply_phase_truth(
    status: &StatusRecord,
    phases: &mut [PhaseView],
) -> Result<(), ProjectionError> {
    let current = phases
        .iter()
        .position(|phase| phase.id == status.current_phase)
        .ok_or(ProjectionError::Inconsistent)?;
    let final_index = phases.len() - 1;
    for (index, phase) in phases.iter_mut().enumerate() {
        if index < current {
            if phase.steps.iter().any(|step| step.state != ViewState::Done) {
                return Err(ProjectionError::Inconsistent);
            }
            phase.state = ViewState::Done;
        } else if index > current {
            if phase
                .steps
                .iter()
                .any(|step| step.state != ViewState::Pending)
            {
                return Err(ProjectionError::Inconsistent);
            }
            phase.state = ViewState::Pending;
        } else if index == final_index {
            let exit = phase
                .steps
                .last()
                .ok_or(ProjectionError::Inconsistent)?
                .state;
            phase.state = if phase.steps.iter().all(|step| step.state == ViewState::Done) {
                ViewState::Done
            } else if exit == ViewState::Error {
                ViewState::Error
            } else {
                ViewState::Active
            };
        } else {
            let exit = phase
                .steps
                .last()
                .ok_or(ProjectionError::Inconsistent)?
                .state;
            if exit == ViewState::Done {
                return Err(ProjectionError::Inconsistent);
            }
            phase.state = if exit == ViewState::Error {
                ViewState::Error
            } else {
                ViewState::Active
            };
        }
    }
    let delivery_ready = step_state(phases, "DELIVERY_PACKAGE_GUARD_READY")?;
    if delivery_ready != ViewState::Done && state(&status.delivery)? != ViewState::Pending {
        return Err(ProjectionError::Inconsistent);
    }
    Ok(())
}

fn state(value: &str) -> Result<ViewState, ProjectionError> {
    match normalize_state(value).ok_or(ProjectionError::Inconsistent)? {
        NormalizedState::Done => Ok(ViewState::Done),
        NormalizedState::Active => Ok(ViewState::Active),
        NormalizedState::Pending => Ok(ViewState::Pending),
        NormalizedState::Error => Ok(ViewState::Error),
    }
}

fn phase(id: &'static str, steps: Vec<StepView>) -> PhaseView {
    PhaseView {
        id,
        state: ViewState::Pending,
        steps,
    }
}

fn step(id: &'static str, state: ViewState, report: Option<&'static str>) -> StepView {
    StepView { id, state, report }
}

fn report(
    id: &'static str,
    state: ViewState,
    version: Option<String>,
    rows: Vec<ReportRow>,
) -> ReportView {
    ReportView {
        id,
        state,
        version,
        rows,
    }
}

fn view_row(key: &'static str, value: ViewState) -> ReportRow {
    ReportRow {
        key,
        value: RowValue::ViewState { value },
    }
}

fn metric_report(id: &'static str, state: ViewState, keys: &[&'static str]) -> ReportView {
    report(
        id,
        state,
        None,
        keys.iter()
            .map(|key| ReportRow {
                key,
                value: RowValue::Metric {
                    status: "NOT_RECORDED",
                    completed: None,
                    total: None,
                    interval_minutes: None,
                },
            })
            .collect(),
    )
}
