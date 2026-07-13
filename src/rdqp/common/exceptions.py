"""Shared application exceptions."""


class RDQPError(Exception):
    """Base exception for RD Quant Platform."""


class ConfigurationError(RDQPError):
    """Raised when configuration cannot be loaded or validated."""


class DependencyResolutionError(RDQPError):
    """Raised when a dependency cannot be resolved."""


class ProviderUnavailableError(RDQPError):
    """Raised when an optional market-data provider is unavailable."""
