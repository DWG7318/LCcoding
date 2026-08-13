use std::fmt;

pub mod compatibility;
pub mod loops;
pub mod manifest;
pub mod maps;
pub mod status;
mod strict_json;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RecordError {
    Invalid,
    UnsupportedVersion,
}

impl RecordError {
    pub const fn code(self) -> &'static str {
        match self {
            Self::Invalid => "BI_RECORD_INVALID",
            Self::UnsupportedVersion => "BI_PROJECT_VERSION_UNSUPPORTED",
        }
    }
}

impl fmt::Display for RecordError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.code())
    }
}

impl std::error::Error for RecordError {}

pub(crate) fn safe_version(value: &str) -> bool {
    let mut chars = value.chars();
    matches!(chars.next(), Some(first) if first.is_ascii_alphanumeric())
        && value.len() <= 32
        && chars.all(|character| {
            character.is_ascii_alphanumeric() || matches!(character, '.' | '_' | '+' | '-')
        })
}
