use serde::Deserialize;

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
    pub compatibility: String,
    pub load_order: Vec<String>,
}

pub fn parse_manifest(text: &str) -> Result<CanonicalManifest, RecordError> {
    let manifest: CanonicalManifest = strict_json::parse(text)?;
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
    digest.len() == 64 && digest.bytes().all(|byte| byte.is_ascii_hexdigit())
}
