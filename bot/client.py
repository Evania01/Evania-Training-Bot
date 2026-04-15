"""Minimal Binance Futures REST client for testnet order placement."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

from bot.exceptions import ApiError, ConfigurationError, NetworkError

DEFAULT_BASE_URL = "https://testnet.binancefuture.com"
DEFAULT_ENV_FILE = ".env"


def load_env_file(path: str = DEFAULT_ENV_FILE) -> None:
    """Load simple KEY=VALUE pairs from a local env file if present."""
    env_path = Path(path)
    if not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key:
            os.environ.setdefault(key, value)


class BinanceFuturesClient:
    """REST client for Binance USDT-M Futures endpoints used by the app."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        base_url: str | None = None,
        env_file: str = DEFAULT_ENV_FILE,
        session: requests.Session | None = None,
        timeout: int = 10,
        logger: logging.Logger | None = None,
    ) -> None:
        load_env_file(env_file)
        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET")
        self.base_url = (base_url or os.getenv("BINANCE_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.session = session or requests.Session()
        self.timeout = timeout
        self.logger = logger or logging.getLogger("trading_bot")
        self._exchange_info_cache: dict[str, Any] | None = None

    def get_exchange_info(self, force_refresh: bool = False) -> dict[str, Any]:
        if self._exchange_info_cache is None or force_refresh:
            self._exchange_info_cache = self._request("GET", "/fapi/v1/exchangeInfo")
        return self._exchange_info_cache

    def get_symbol_info(self, symbol: str) -> dict[str, Any] | None:
        exchange_info = self.get_exchange_info()
        for item in exchange_info.get("symbols", []):
            if item.get("symbol") == symbol:
                return item
        return None

    def create_order(self, params: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/fapi/v1/order", params=params, signed=True)

    def query_order(self, symbol: str, order_id: int | str) -> dict[str, Any]:
        params = {"symbol": symbol, "orderId": order_id}
        return self._request("GET", "/fapi/v1/order", params=params, signed=True)

    def validate_credentials(self) -> None:
        self._ensure_credentials()

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        signed: bool = False,
    ) -> dict[str, Any]:
        request_params = {key: value for key, value in (params or {}).items() if value is not None}

        headers: dict[str, str] = {}
        if signed:
            self._ensure_credentials()
            request_params.setdefault("recvWindow", 5000)
            request_params["timestamp"] = int(time.time() * 1000)
            query = urlencode(request_params, doseq=True)
            request_params["signature"] = self._sign(query)
            headers["X-MBX-APIKEY"] = self.api_key or ""

        url = f"{self.base_url}{path}"
        self._log_request(method, path, request_params)

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=request_params,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            self.logger.error(
                "network_error method=%s path=%s error=%s",
                method,
                path,
                exc,
            )
            raise NetworkError(f"Network failure while calling Binance: {exc}") from exc

        return self._parse_response(method, path, response)

    def _parse_response(
        self,
        method: str,
        path: str,
        response: requests.Response,
    ) -> dict[str, Any]:
        try:
            data = response.json()
        except ValueError as exc:
            self.logger.error(
                "invalid_json method=%s path=%s status=%s body=%s",
                method,
                path,
                response.status_code,
                response.text,
            )
            raise NetworkError("Binance returned a non-JSON response.") from exc

        self.logger.info(
            "response method=%s path=%s status=%s body=%s",
            method,
            path,
            response.status_code,
            self._summarize_response_body(path, data),
        )

        if not response.ok:
            error_code = data.get("code") if isinstance(data, dict) else None
            message = data.get("msg", "Unknown Binance API error") if isinstance(data, dict) else str(data)
            raise ApiError(
                status_code=response.status_code,
                error_code=error_code,
                message=message,
                response_body=data,
            )

        if not isinstance(data, dict):
            raise NetworkError("Unexpected response shape from Binance.")

        return data

    def _ensure_credentials(self) -> None:
        if not self.api_key or not self.api_secret:
            raise ConfigurationError(
                "BINANCE_API_KEY and BINANCE_API_SECRET must be set for signed endpoints."
            )

    def _sign(self, query: str) -> str:
        secret = (self.api_secret or "").encode("utf-8")
        return hmac.new(secret, query.encode("utf-8"), hashlib.sha256).hexdigest()

    def _log_request(self, method: str, path: str, params: dict[str, Any]) -> None:
        self.logger.info(
            "request method=%s path=%s params=%s",
            method,
            path,
            self._sanitize_params(params),
        )

    @staticmethod
    def _sanitize_params(params: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in params.items()
            if key not in {"signature", "apiKey", "secret", "api_secret"}
        }

    @staticmethod
    def _summarize_response_body(path: str, data: dict[str, Any]) -> str | dict[str, Any]:
        if path == "/fapi/v1/exchangeInfo":
            return {
                "timezone": data.get("timezone"),
                "serverTime": data.get("serverTime"),
                "futuresType": data.get("futuresType"),
                "symbolsCount": len(data.get("symbols", [])),
            }

        serialized = json.dumps(data, sort_keys=True)
        if len(serialized) > 1200:
            return f"{serialized[:1200]}... [truncated]"
        return data
