use std::fmt;


#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum BindError {
    ArgumentInvalid,
    RootInvalid,
    ProjectAlreadyBound,
    ProjectNotBound,
}

impl BindError {
    pub const fn code(self) -> &'static str {
        match self {
            Self::ArgumentInvalid => "BI_ARGUMENT_INVALID",
            Self::RootInvalid => "BI_ROOT_INVALID",
            Self::ProjectAlreadyBound => "BI_PROJECT_ALREADY_BOUND",
            Self::ProjectNotBound => "BI_NO_PROJECT",
        }
    }
}

impl fmt::Display for BindError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.code())
    }
}

impl std::error::Error for BindError {}
