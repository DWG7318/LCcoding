use serde::Serialize;

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum ViewState {
    Done,
    Active,
    Pending,
    Error,
}

#[derive(Debug, Serialize)]
pub struct Snapshot {
    pub schema: &'static str,
    pub authoritative: bool,
    pub read_only: bool,
    pub health: &'static str,
    pub project: String,
    pub current_phase: String,
    pub phases: Vec<PhaseView>,
    pub reports: Reports,
}

#[derive(Debug, Serialize)]
pub struct PhaseView {
    pub id: &'static str,
    pub state: ViewState,
    pub steps: Vec<StepView>,
}

#[derive(Debug, Serialize)]
pub struct StepView {
    pub id: &'static str,
    pub state: ViewState,
    pub report: Option<&'static str>,
}

#[derive(Debug, Serialize)]
pub struct Reports {
    pub proposal: ReportView,
    pub candidate: ReportView,
    pub calabash: ReportView,
    pub simulation: ReportView,
    pub workflow: ReportView,
    pub ui: ReportView,
    pub baseline: ReportView,
    pub loop_governance: ReportView,
}

#[derive(Debug, Serialize)]
pub struct ReportView {
    pub id: &'static str,
    pub state: ViewState,
    pub version: Option<String>,
    pub rows: Vec<ReportRow>,
}

#[derive(Debug, Serialize)]
pub struct ReportRow {
    pub key: &'static str,
    pub value: RowValue,
}

#[derive(Debug, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum RowValue {
    ViewState {
        value: ViewState,
    },
    Phase {
        value: String,
    },
    Lock {
        value: &'static str,
    },
    Record {
        value: &'static str,
    },
    Metric {
        status: &'static str,
        completed: Option<u32>,
        total: Option<u32>,
        interval_minutes: Option<u8>,
    },
}
