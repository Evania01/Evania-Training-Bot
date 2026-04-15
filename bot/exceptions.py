"""Custom exception types for the trading bot."""


class TradingBotError(Exception):
    """Base exception for all application-specific failures."""


class ConfigurationError(TradingBotError):
    """Raised when required local configuration is missing."""


class ValidationError(TradingBotError):
    """Raised when CLI inputs do not meet application or exchange rules."""


class ApiError(TradingBotError):
    """Raised when Binance returns an API-level failure."""

    def __init__(
        self,
        status_code: int,
        error_code: int | str | None,
        message: str,
        response_body: object | None = None,
    ) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.response_body = response_body
        super().__init__(self.__str__())

    def __str__(self) -> str:
        base = f"API error (HTTP {self.status_code})"
        if self.error_code is not None:
            base += f" [code={self.error_code}]"
        return f"{base}: {self.message}"


class NetworkError(TradingBotError):
    """Raised when the app cannot reach Binance or parse the response."""
