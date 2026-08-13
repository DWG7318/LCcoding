use std::collections::HashSet;

use serde::{Deserialize, Deserializer};

use super::{RecordError, safe_version, strict_json};

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct MethodIdentity {
    pub version: String,
    pub hash: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CanonicalManifest {
    pub lccoding: MethodIdentity,
    pub calabash: MethodIdentity,
    pub slk: MethodIdentity,
    pub clk: MethodIdentity,
    pub glk: MethodIdentity,
    #[serde(default)]
    execution_methods: Present<Vec<ExecutionMethod>>,
    pub compatibility: String,
    pub load_order: Vec<String>,
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

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ExecutionMethod {
    pub method_id: String,
    pub version: String,
    pub exact_hash: String,
    pub canonical_contract_reference: String,
    pub run_evidence_mapping: String,
    pub owner_acceptance_mapping: String,
    pub required_control_binding: String,
    pub compatibility_result: String,
}

pub fn parse_manifest(text: &str) -> Result<CanonicalManifest, RecordError> {
    let manifest: CanonicalManifest = strict_json::parse(text)?;
    let execution_methods = match &manifest.execution_methods {
        Present::Value(methods) => methods.as_slice(),
        Present::Missing if manifest.lccoding.version == "2.6.0" => &[],
        Present::Missing => return Err(RecordError::Invalid),
    };
    for method in [
        &manifest.lccoding,
        &manifest.calabash,
        &manifest.slk,
        &manifest.clk,
        &manifest.glk,
    ] {
        if (!method.version.is_empty() && !safe_version(&method.version))
            || (!method.hash.is_empty() && !safe_hash(&method.hash))
        {
            return Err(RecordError::Invalid);
        }
    }
    let mut method_ids = HashSet::new();
    for method in execution_methods {
        if !method_ids.insert(&method.method_id)
            || !safe_id(&method.method_id)
            || !semantic_version(&method.version)
            || !safe_prefixed_hash(&method.exact_hash)
            || !safe_reference(&method.canonical_contract_reference)
            || !safe_mapping(&method.run_evidence_mapping)
            || !safe_mapping(&method.owner_acceptance_mapping)
            || method.required_control_binding != "LCCODING_LOOP_CONTROL"
            || !matches!(method.compatibility_result.as_str(), "PASS" | "BLOCKED")
        {
            return Err(RecordError::Invalid);
        }
    }
    if manifest.compatibility.is_empty()
        || manifest.compatibility.len() > 64
        || !manifest
            .compatibility
            .bytes()
            .enumerate()
            .all(|(index, byte)| {
                if index == 0 {
                    byte.is_ascii_uppercase()
                } else {
                    byte.is_ascii_uppercase() || byte.is_ascii_digit() || byte == b'_'
                }
            })
        || manifest.load_order.iter().any(|value| {
            value.is_empty()
                || value.len() > 64
                || value.chars().any(|character| character.is_control())
        })
    {
        return Err(RecordError::Invalid);
    }
    Ok(manifest)
}

fn safe_hash(value: &str) -> bool {
    let digest = value.strip_prefix("sha256:").unwrap_or(value);
    digest.len() == 64
        && digest
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
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

fn safe_id(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 96
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'))
}

fn safe_prefixed_hash(value: &str) -> bool {
    value.strip_prefix("sha256:").is_some_and(|digest| {
        digest.len() == 64
            && digest
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    })
}

fn safe_reference(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 256
        && !value.starts_with('/')
        && !value.contains("..")
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'/' | b'.' | b'_' | b'-'))
}

fn safe_mapping(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 256
        && value.chars().all(|character| {
            !character.is_control()
                && !matches!(
                    character,
                    '\u{200e}' | '\u{200f}' | '\u{202a}'..='\u{202e}' | '\u{2066}'..='\u{2069}'
                )
        })
}
