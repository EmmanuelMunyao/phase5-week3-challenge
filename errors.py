class AppError(Exception):
    """Base exception for application errors."""


class ConfigurationError(AppError):
    """Raised when application configuration is invalid."""


class InputError(AppError):
    """Raised when user input is invalid."""


class ExternalServiceError(AppError):
    """Raised when an external service fails."""