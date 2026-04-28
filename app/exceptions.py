class AppError(Exception):
    """Application-level base exception."""


class ExternalServiceError(AppError):
    """Raised when an upstream API call fails."""


class ConfigurationError(AppError):
    """Raised when required runtime configuration is missing."""
