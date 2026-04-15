"""Order placement service built on top of the Binance REST client."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from bot.validators import validate_order_inputs


class OrderService:
    """Coordinates validation, request building, and response normalization."""

    def __init__(self, client: Any) -> None:
        self.client = client

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str,
        price: str | None = None,
    ) -> dict[str, Any]:
        normalized_symbol = str(symbol).strip().upper()
        symbol_info = self.client.get_symbol_info(normalized_symbol)
        validated = validate_order_inputs(
            symbol_info=symbol_info,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )

        request_summary = self._build_request_summary(validated)
        payload = self._build_order_payload(validated)

        response = self.client.create_order(payload)
        normalized_response = self._normalize_response(validated["symbol"], response)

        return {
            "request": request_summary,
            "response": normalized_response,
            "raw_response": response,
        }

    def _build_order_payload(self, validated: dict[str, Any]) -> dict[str, str]:
        payload = {
            "symbol": validated["symbol"],
            "side": validated["side"],
            "type": validated["order_type"],
            "quantity": decimal_to_string(validated["quantity"]),
            "newOrderRespType": "RESULT",
        }

        if validated["order_type"] == "LIMIT":
            payload["price"] = decimal_to_string(validated["price"])
            payload["timeInForce"] = "GTC"

        return payload

    def _build_request_summary(self, validated: dict[str, Any]) -> dict[str, str | None]:
        return {
            "symbol": validated["symbol"],
            "side": validated["side"],
            "type": validated["order_type"],
            "quantity": decimal_to_string(validated["quantity"]),
            "price": (
                decimal_to_string(validated["price"])
                if validated["price"] is not None
                else None
            ),
        }

    def _normalize_response(
        self,
        symbol: str,
        response: dict[str, Any],
    ) -> dict[str, Any]:
        merged_response = dict(response)
        order_id = merged_response.get("orderId")
        if order_id is not None and self._response_needs_enrichment(merged_response):
            latest = self.client.query_order(symbol, order_id)
            merged_response.update(latest)

        return {
            "symbol": merged_response.get("symbol", symbol),
            "orderId": merged_response.get("orderId"),
            "status": merged_response.get("status", "UNKNOWN"),
            "executedQty": _string_or_na(merged_response.get("executedQty")),
            "avgPrice": _string_or_na(merged_response.get("avgPrice")),
            "price": _string_or_na(merged_response.get("price")),
            "side": merged_response.get("side"),
            "type": merged_response.get("type"),
        }

    @staticmethod
    def _response_needs_enrichment(response: dict[str, Any]) -> bool:
        required_fields = ("status", "executedQty")
        for field in required_fields:
            if response.get(field) in (None, ""):
                return True
        return response.get("avgPrice") in (None, "")


def decimal_to_string(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _string_or_na(value: Any) -> str:
    if value in (None, ""):
        return "N/A"
    return str(value)
