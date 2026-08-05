use std::collections::HashSet;

use super::RecordError;

const MAX_ROWS: usize = 256;
const NOT_APPLICABLE: &str = "NOT_APPLICABLE";

const WORKFLOW_HEADER: [&str; 18] = [
    "Workflow ID",
    "Classification (CORE/EXTRA)",
    "Implementation status",
    "Subtree path",
    "Component version",
    "Content hash",
    "Actors",
    "Trigger",
    "States / rules",
    "Data / permissions",
    "Failure / recovery",
    "API contract / evidence",
    "MCP contract / evidence",
    "UI subtree references",
    "Simulation subtree references",
    "Evidence / attestation",
    "Calabash trace",
    "Primary mainline",
];
const UI_HEADER: [&str; 12] = [
    "UI ID",
    "Subtree path",
    "Component version",
    "Content hash",
    "Actor",
    "Surface / state",
    "Actions / feedback",
    "Workflow subtree references",
    "Simulation subtree references",
    "Evidence / attestation",
    "Lock status",
    "Primary mainline",
];
const SIMULATION_HEADER: [&str; 8] = [
    "Simulation ID",
    "Subtree path",
    "Component version",
    "Content hash",
    "Foundation status",
    "Workflow subtree references",
    "UI subtree references",
    "Primary mainline",
];
const HANDOFF_HEADER: [&str; 10] = [
    "Subtree type",
    "Subtree ID",
    "Path",
    "Component version",
    "Content hash",
    "Classification",
    "API evidence",
    "MCP evidence",
    "Primary mainline",
    "Related subtree IDs",
];

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Classification {
    Core,
    Extra,
}

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum SubtreeType {
    Workflow,
    Ui,
    Simulation,
}

#[derive(Debug)]
pub struct WorkflowRow {
    pub id: String,
    pub classification: Classification,
    pub implemented: bool,
    pub path: Option<String>,
    pub version: Option<String>,
    pub content_hash: Option<String>,
    pub api_evidence: Option<String>,
    pub mcp_evidence: Option<String>,
    pub ui_refs: Vec<String>,
    pub simulation_refs: Vec<String>,
    pub primary: bool,
}

#[derive(Debug)]
pub struct WorkflowMap {
    pub mainline_id: String,
    pub rows: Vec<WorkflowRow>,
}

#[derive(Debug)]
pub struct UiRow {
    pub id: String,
    pub path: String,
    pub version: String,
    pub content_hash: String,
    pub workflow_refs: Vec<String>,
    pub simulation_refs: Vec<String>,
    pub lock_status: String,
    pub primary: bool,
}

#[derive(Debug)]
pub struct UiMap {
    pub mainline_id: String,
    pub rows: Vec<UiRow>,
}

#[derive(Debug)]
pub struct SimulationRow {
    pub id: String,
    pub path: String,
    pub version: String,
    pub content_hash: String,
    pub foundation_status: String,
    pub workflow_refs: Vec<String>,
    pub ui_refs: Vec<String>,
    pub primary: bool,
}

#[derive(Debug)]
pub struct SimulationMap {
    pub mainline_id: String,
    pub rows: Vec<SimulationRow>,
}

#[derive(Debug)]
pub struct HandoffRow {
    pub subtree_type: SubtreeType,
    pub id: String,
    pub path: String,
    pub version: String,
    pub content_hash: String,
    pub classification: Option<Classification>,
    pub api_evidence: Option<String>,
    pub mcp_evidence: Option<String>,
    pub primary: bool,
    pub related_ids: Vec<String>,
}

#[derive(Debug)]
pub struct ProductBaselineHandoff {
    pub repository_identity: String,
    pub frozen_commit: String,
    pub mainline_id: String,
    pub owner_confirmation: String,
    pub complete: bool,
    pub rows: Vec<HandoffRow>,
}

pub fn parse_workflow_map(text: &str) -> Result<WorkflowMap, RecordError> {
    let rows = table(text, &WORKFLOW_HEADER)?;
    let mut ids = HashSet::new();
    let mut paths = HashSet::new();
    let mut parsed = Vec::with_capacity(rows.len());
    for row in rows {
        let id = identifier(&row[0])?;
        if !ids.insert(id.clone()) {
            return Err(RecordError::Invalid);
        }
        let classification = classification(&row[1])?;
        let implemented = match row[2].as_str() {
            "IMPLEMENTED" => true,
            "UNIMPLEMENTED" => false,
            _ => return Err(RecordError::Invalid),
        };
        let primary = yes_no(&row[17])?;
        let (path, version, content_hash, api_evidence, mcp_evidence) = if implemented {
            let path = subtree_path(&row[3])?;
            if !paths.insert(path.clone()) {
                return Err(RecordError::Invalid);
            }
            (
                Some(path),
                Some(component_version(&row[4])?),
                Some(content_hash(&row[5])?),
                optional_evidence(&row[11])?,
                optional_evidence(&row[12])?,
            )
        } else {
            if [&row[3], &row[4], &row[5], &row[11], &row[12]]
                .into_iter()
                .any(|value| value != NOT_APPLICABLE)
            {
                return Err(RecordError::Invalid);
            }
            (None, None, None, None, None)
        };
        if primary && (!implemented || classification != Classification::Core) {
            return Err(RecordError::Invalid);
        }
        parsed.push(WorkflowRow {
            id,
            classification,
            implemented,
            path,
            version,
            content_hash,
            api_evidence,
            mcp_evidence,
            ui_refs: references(&row[13])?,
            simulation_refs: references(&row[14])?,
            primary,
        });
    }
    Ok(WorkflowMap {
        mainline_id: mainline_id(text)?,
        rows: parsed,
    })
}

pub fn parse_ui_map(text: &str) -> Result<UiMap, RecordError> {
    let rows = table(text, &UI_HEADER)?;
    let mut ids = HashSet::new();
    let mut paths = HashSet::new();
    let mut parsed = Vec::with_capacity(rows.len());
    for row in rows {
        let id = identifier(&row[0])?;
        let path = subtree_path(&row[1])?;
        if !ids.insert(id.clone()) || !paths.insert(path.clone()) {
            return Err(RecordError::Invalid);
        }
        if !matches!(
            row[10].as_str(),
            "LOCKED" | "PENDING" | "UNKNOWN" | "BLOCKED"
        ) {
            return Err(RecordError::Invalid);
        }
        parsed.push(UiRow {
            id,
            path,
            version: component_version(&row[2])?,
            content_hash: content_hash(&row[3])?,
            workflow_refs: references(&row[7])?,
            simulation_refs: references(&row[8])?,
            lock_status: row[10].clone(),
            primary: yes_no(&row[11])?,
        });
    }
    Ok(UiMap {
        mainline_id: mainline_id(text)?,
        rows: parsed,
    })
}

pub fn parse_simulation_map(text: &str) -> Result<SimulationMap, RecordError> {
    let rows = table(text, &SIMULATION_HEADER)?;
    let mut ids = HashSet::new();
    let mut paths = HashSet::new();
    let mut parsed = Vec::with_capacity(rows.len());
    for row in rows {
        let id = identifier(&row[0])?;
        let path = subtree_path(&row[1])?;
        if !ids.insert(id.clone()) || !paths.insert(path.clone()) {
            return Err(RecordError::Invalid);
        }
        if !matches!(
            row[4].as_str(),
            "REALIZED" | "COMPLETE" | "ACTIVE" | "PENDING" | "UNKNOWN" | "BLOCKED"
        ) {
            return Err(RecordError::Invalid);
        }
        parsed.push(SimulationRow {
            id,
            path,
            version: component_version(&row[2])?,
            content_hash: content_hash(&row[3])?,
            foundation_status: row[4].clone(),
            workflow_refs: references(&row[5])?,
            ui_refs: references(&row[6])?,
            primary: yes_no(&row[7])?,
        });
    }
    for (index, row) in parsed.iter().enumerate() {
        for other in parsed.iter().skip(index + 1) {
            if nested(&row.path, &other.path) {
                return Err(RecordError::Invalid);
            }
        }
    }
    Ok(SimulationMap {
        mainline_id: mainline_id(text)?,
        rows: parsed,
    })
}

pub fn parse_handoff(text: &str) -> Result<ProductBaselineHandoff, RecordError> {
    let repository_identity = field(text, "Project repository identity")?;
    if repository_identity.len() > 256 || !repository_identity.starts_with("github.com/") {
        return Err(RecordError::Invalid);
    }
    let frozen_commit = field(text, "Project frozen exact commit SHA")?;
    if frozen_commit.len() != 40 || !frozen_commit.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(RecordError::Invalid);
    }
    let mainline_id = identifier(&field(text, "Primary product mainline ID")?)?;
    let owner_confirmation = field(text, "Primary mainline Owner confirmation")?;
    if !owner_confirmation
        .strip_prefix("OWNER_CONFIRMED:")
        .is_some_and(|value| !value.trim().is_empty())
    {
        return Err(RecordError::Invalid);
    }
    let complete = match field(text, "Handoff status")?.as_str() {
        "COMPLETE" => true,
        "BLOCKED" => false,
        _ => return Err(RecordError::Invalid),
    };

    let rows = table(text, &HANDOFF_HEADER)?;
    let mut ids = HashSet::new();
    let mut paths = HashSet::new();
    let mut parsed = Vec::with_capacity(rows.len());
    for row in rows {
        let subtree_type = match row[0].as_str() {
            "WORKFLOW" => SubtreeType::Workflow,
            "UI" => SubtreeType::Ui,
            "SIMULATION" => SubtreeType::Simulation,
            _ => return Err(RecordError::Invalid),
        };
        let id = identifier(&row[1])?;
        let path = subtree_path(&row[2])?;
        if !ids.insert(id.clone()) || !paths.insert(path.clone()) {
            return Err(RecordError::Invalid);
        }
        let (classification, api_evidence, mcp_evidence) = if subtree_type == SubtreeType::Workflow
        {
            (
                Some(classification(&row[5])?),
                Some(required_evidence(&row[6])?),
                Some(required_evidence(&row[7])?),
            )
        } else {
            if [&row[5], &row[6], &row[7]]
                .into_iter()
                .any(|value| value != NOT_APPLICABLE)
            {
                return Err(RecordError::Invalid);
            }
            (None, None, None)
        };
        parsed.push(HandoffRow {
            subtree_type,
            id,
            path,
            version: component_version(&row[3])?,
            content_hash: content_hash(&row[4])?,
            classification,
            api_evidence,
            mcp_evidence,
            primary: yes_no(&row[8])?,
            related_ids: references(&row[9])?,
        });
    }
    Ok(ProductBaselineHandoff {
        repository_identity,
        frozen_commit,
        mainline_id,
        owner_confirmation,
        complete,
        rows: parsed,
    })
}

fn table(text: &str, header: &[&str]) -> Result<Vec<Vec<String>>, RecordError> {
    let lines = text.lines().collect::<Vec<_>>();
    let matches = lines
        .iter()
        .enumerate()
        .filter_map(|(index, line)| {
            cells(line)
                .is_some_and(|cells| cells.iter().map(String::as_str).eq(header.iter().copied()))
                .then_some(index)
        })
        .collect::<Vec<_>>();
    if matches.len() != 1 {
        return Err(RecordError::Invalid);
    }
    let start = matches[0];
    let separator = lines
        .get(start + 1)
        .and_then(|line| cells(line))
        .ok_or(RecordError::Invalid)?;
    if separator.len() != header.len()
        || separator
            .iter()
            .any(|cell| cell.len() < 3 || !cell.bytes().all(|byte| byte == b'-'))
    {
        return Err(RecordError::Invalid);
    }
    let mut rows = Vec::new();
    for line in lines.iter().skip(start + 2) {
        if !line.trim_start().starts_with('|') {
            break;
        }
        let row = cells(line).ok_or(RecordError::Invalid)?;
        if row.len() != header.len() || row.iter().any(|value| !safe_cell(value)) {
            return Err(RecordError::Invalid);
        }
        rows.push(row);
        if rows.len() > MAX_ROWS {
            return Err(RecordError::Invalid);
        }
    }
    Ok(rows)
}

fn cells(line: &str) -> Option<Vec<String>> {
    let value = line.trim();
    value
        .strip_prefix('|')?
        .strip_suffix('|')
        .map(|body| body.split('|').map(|cell| cell.trim().to_owned()).collect())
}

fn field(text: &str, name: &str) -> Result<String, RecordError> {
    let prefix = format!("- {name}:");
    let values = text
        .lines()
        .filter_map(|line| line.trim().strip_prefix(&prefix).map(str::trim))
        .collect::<Vec<_>>();
    if values.len() != 1 || !safe_cell(values[0]) || values[0].is_empty() {
        return Err(RecordError::Invalid);
    }
    Ok(values[0].to_owned())
}

fn mainline_id(text: &str) -> Result<String, RecordError> {
    identifier(&field(text, "Primary product mainline ID")?)
}

fn identifier(value: &str) -> Result<String, RecordError> {
    if value.is_empty()
        || value.len() > 64
        || !value.as_bytes()[0].is_ascii_alphanumeric()
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'))
    {
        return Err(RecordError::Invalid);
    }
    Ok(value.to_owned())
}

fn subtree_path(value: &str) -> Result<String, RecordError> {
    if value.is_empty()
        || value.len() > 256
        || value.starts_with('/')
        || value.contains(['\\', ':', '\0'])
        || !safe_cell(value)
        || value
            .split('/')
            .any(|part| part.is_empty() || matches!(part, "." | ".."))
    {
        return Err(RecordError::Invalid);
    }
    Ok(value.to_owned())
}

fn component_version(value: &str) -> Result<String, RecordError> {
    let (core, prerelease) = value
        .split_once('-')
        .map_or((value, None), |(core, tail)| (core, Some(tail)));
    let parts = core.split('.').collect::<Vec<_>>();
    let valid_core = parts.len() == 3
        && parts
            .iter()
            .all(|part| !part.is_empty() && part.bytes().all(|byte| byte.is_ascii_digit()));
    let valid_prerelease = prerelease.is_none_or(|tail| {
        !tail.is_empty()
            && tail.len() <= 32
            && tail
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'-'))
    });
    if !valid_core || !valid_prerelease || value.len() > 64 {
        return Err(RecordError::Invalid);
    }
    Ok(value.to_owned())
}

fn content_hash(value: &str) -> Result<String, RecordError> {
    let digest = value.strip_prefix("sha256:").ok_or(RecordError::Invalid)?;
    if digest.len() != 64 || !digest.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(RecordError::Invalid);
    }
    Ok(format!("sha256:{}", digest.to_ascii_lowercase()))
}

fn classification(value: &str) -> Result<Classification, RecordError> {
    match value {
        "CORE" => Ok(Classification::Core),
        "EXTRA" => Ok(Classification::Extra),
        _ => Err(RecordError::Invalid),
    }
}

fn yes_no(value: &str) -> Result<bool, RecordError> {
    match value {
        "YES" => Ok(true),
        "NO" => Ok(false),
        _ => Err(RecordError::Invalid),
    }
}

fn references(value: &str) -> Result<Vec<String>, RecordError> {
    if value == "NONE" {
        return Ok(Vec::new());
    }
    let mut seen = HashSet::new();
    let mut values = Vec::new();
    for value in value.split(',').map(str::trim) {
        let value = identifier(value)?;
        if !seen.insert(value.clone()) {
            return Err(RecordError::Invalid);
        }
        values.push(value);
    }
    if values.is_empty() || values.len() > 64 {
        return Err(RecordError::Invalid);
    }
    Ok(values)
}

fn optional_evidence(value: &str) -> Result<Option<String>, RecordError> {
    if matches!(value, "PENDING" | "UNKNOWN" | "NONE" | NOT_APPLICABLE) {
        Ok(None)
    } else {
        required_evidence(value).map(Some)
    }
}

fn required_evidence(value: &str) -> Result<String, RecordError> {
    if !safe_cell(value)
        || value.is_empty()
        || matches!(value, "PENDING" | "UNKNOWN" | "NONE" | NOT_APPLICABLE)
    {
        return Err(RecordError::Invalid);
    }
    Ok(value.to_owned())
}

fn safe_cell(value: &str) -> bool {
    value.len() <= 1_024
        && value.chars().all(|character| {
            !character.is_control()
                && !matches!(
                    character,
                    '\u{200e}' | '\u{200f}' | '\u{202a}'..='\u{202e}' | '\u{2066}'..='\u{2069}'
                )
        })
}

fn nested(left: &str, right: &str) -> bool {
    left.starts_with(&format!("{right}/")) || right.starts_with(&format!("{left}/"))
}
