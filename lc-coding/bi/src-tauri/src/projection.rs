use std::collections::{HashMap, HashSet};
use std::fmt;
use std::path::{Path, PathBuf};

use crate::git_reader::GitProject;
use crate::input::{ProjectRecord, read_optional_scoped_record, read_project_record};
use crate::records::loops::{
    CLK_MANIFEST_SHA256, CLK_VERSION, GLK_MANIFEST_SHA256, GLK_VERSION, GlkArtifact,
    GovernanceStatus, GovernanceSummary, SLK_MANIFEST_SHA256, SLK_VERSION, glk_artifact_refs,
    parse_clk_governance, parse_glk_governance, parse_slk_governance,
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
            require_method_identity(
                &manifest.slk.version,
                &manifest.slk.hash,
                SLK_VERSION,
                SLK_MANIFEST_SHA256,
            )?;
            parse_slk_governance(&body).map_err(|error| ProjectLoadError { code: error.code() })?
        } else if let Some(body) = clk {
            require_method_identity(
                &manifest.clk.version,
                &manifest.clk.hash,
                CLK_VERSION,
                CLK_MANIFEST_SHA256,
            )?;
            parse_clk_governance(&body).map_err(|error| ProjectLoadError { code: error.code() })?
        } else {
            let body = glk.expect("exactly one loop index");
            require_method_identity(
                &manifest.glk.version,
                &manifest.glk.hash,
                GLK_VERSION,
                GLK_MANIFEST_SHA256,
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

pub fn snapshot_from_status(
    status: &StatusRecord,
    manifest: Option<&CanonicalManifest>,
) -> Result<Snapshot, ProjectionError> {
    if manifest.is_some_and(|manifest| manifest.lccoding.version != status.status_schema_version) {
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

    let mut phases = vec![
        phase(
            "INITIAL",
            vec![
                step(
                    "PROPOSAL_READINESS",
                    state(&status.proposal)?,
                    Some("proposal"),
                ),
                step(
                    "PROJECT_INITIALIZATION",
                    state(&status.initialization)?,
                    Some("candidate"),
                ),
                step(
                    "INITIAL_READY",
                    state(&status.phase_gates.initial_ready)?,
                    None,
                ),
            ],
        ),
        phase(
            "PRODUCT_FORMATION",
            vec![
                step(
                    "CALABASH_DRAFT",
                    state(&status.calabash_draft)?,
                    Some("calabash"),
                ),
                step(
                    "SIMULATION_WORLD_FOUNDATION",
                    state(&status.simulation)?,
                    Some("simulation"),
                ),
                step(
                    "WORKFLOW_CAPABILITY_END",
                    state(&status.workflow)?,
                    Some("workflow"),
                ),
                step("UI_PRODUCT_SURFACE_END", state(&status.ui)?, Some("ui")),
                step(
                    "CALABASH_UPGRADE_READY",
                    state(&status.phase_gates.calabash_upgrade_ready)?,
                    None,
                ),
            ],
        ),
        phase(
            "ENGINEERING_RUNS",
            vec![
                step(
                    "MANDATORY_CALABASH_UPGRADE",
                    state(&status.mandatory_calabash_upgrade)?,
                    None,
                ),
                step(
                    "PRODUCT_BASELINE",
                    state(&status.product_baseline)?,
                    Some("baseline"),
                ),
                step("FEATURE_SLICE_EXECUTION_COVERAGE", feature_slice, None),
                step("UI_LOCKED_INTEGRATION_BASELINE", integration, None),
                step("LOOP_RUN_D0_D3", run, Some("loop_governance")),
                step("LOOP_OWNER_ACCEPTANCE", acceptance, None),
                step("ALL_REQUIRED_RUNS_ACCEPTED", aggregate, None),
            ],
        ),
        phase(
            "DELIVERY_PREPARATION",
            vec![
                step(
                    "CENTRALIZED_VULNERABILITY_AUDIT",
                    state(&status.centralized_security_audit)?,
                    None,
                ),
                step(
                    "SECURITY_REMEDIATION",
                    state(&status.security_remediation)?,
                    None,
                ),
                step(
                    "SECURITY_REAUDIT_VULNERABILITY_CLOSURE",
                    state(&status.vulnerability_closure)?,
                    None,
                ),
                step(
                    "POST_SECURITY_OWNER_ACCEPTANCE",
                    state(&status.post_security_owner_acceptance)?,
                    None,
                ),
                step(
                    "DELIVERY_METHOD_QA",
                    state(&status.delivery_method_qa)?,
                    None,
                ),
                step(
                    "DELIVERY_PACKAGE_GUARD_READY",
                    state(&status.phase_gates.delivery_ready)?,
                    None,
                ),
            ],
        ),
    ];
    apply_phase_truth(status, &mut phases)?;

    let candidate_locked = !status.canonical_candidate.repository.is_empty();
    let calabash_version = manifest.and_then(|manifest| {
        (!manifest.calabash.version.is_empty()).then(|| manifest.calabash.version.clone())
    });
    let reports = Reports {
        proposal: report(
            "proposal",
            phases[0].steps[0].state,
            None,
            vec![
                view_row("row.conclusion", phases[0].steps[0].state),
                view_row("row.initial_gate", phases[0].steps[2].state),
            ],
        ),
        candidate: report(
            "candidate",
            phases[0].steps[1].state,
            candidate_locked.then(|| status.canonical_candidate.version.clone()),
            vec![
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
                        value: if candidate_locked && phases[0].steps[1].state == ViewState::Done {
                            "RECORDED"
                        } else {
                            "PENDING"
                        },
                    },
                },
            ],
        ),
        calabash: report(
            "calabash",
            phases[1].steps[0].state,
            calabash_version.clone(),
            vec![
                view_row("row.status", phases[1].steps[0].state),
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
            phases[1].steps[1].state,
            &[
                "row.realized_peer_subtrees",
                "row.component_version_coverage",
                "row.primary_mainline",
            ],
        ),
        workflow: metric_report(
            "workflow",
            phases[1].steps[2].state,
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
            phases[1].steps[3].state,
            &[
                "row.realized_subtrees",
                "row.component_version_coverage",
                "row.lock_status",
                "row.primary_mainline",
            ],
        ),
        baseline: metric_report(
            "baseline",
            phases[2].steps[1].state,
            &[
                "row.git_identity",
                "row.locked_subtree_coverage",
                "row.map_handoff_consistency",
                "row.owner_confirmed_mainline",
            ],
        ),
        loop_governance: metric_report(
            "loop_governance",
            phases[2].steps[4].state,
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
        schema: "LCCoding 2.5.1 derived BI",
        authoritative: false,
        read_only: true,
        health: "ok",
        project: status.project_id.clone(),
        current_phase: status.current_phase.clone(),
        phases,
        reports,
    })
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
    let delivery_ready = phases[3].steps[5].state;
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
