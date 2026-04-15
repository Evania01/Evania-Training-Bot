"""Validation helpers for CLI inputs and exchange symbol rules."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from bot.exceptions import ValidationError

ALLOWED_SIDES = {"BUY", "SELL"}
ALLOWED_ORDER_TYPES = {"MARKET", "LIMIT"}


def validate_order_inputs(
    symbol_info: dict[str, Any] | None,
    side: str,
    order_type: str,
    quantity: str,
    price: str | None = None,
) -> dict[str, Decimal | str | None]:
    if symbol_info is None:
        raise ValidationError("Symbol is not available on Binance Futures Testnet.")

    symbol = str(symbol_info.get("symbol", "")).upper()
    if symbol_info.get("status") != "TRADING":
        raise ValidationError(f"Symbol {symbol} is not currently tradable.")
    if symbol_info.get("quoteAsset") != "USDT" or symbol_info.get("marginAsset") != "USDT":
        raise ValidationError(f"Symbol {symbol} is not a USDT-M futures contract.")

    side = normalize_choice(side, ALLOWED_SIDES, "side")
    order_type = normalize_choice(order_type, ALLOWED_ORDER_TYPES, "order type")
    quantity_decimal = parse_positive_decimal(quantity, "quantity")

    price_decimal: Decimal | None = None
    if order_type == "LIMIT":
        if price is None:
            raise ValidationError("price is required for LIMIT orders.")
        price_decimal = parse_positive_decimal(price, "price")
    elif price is not None:
        raise ValidationError("price must not be supplied for MARKET orders.")

    quantity_filter = _get_quantity_filter(symbol_info, order_type)
    _validate_filter_range(quantity_decimal, quantity_filter, "quantity", "minQty", "maxQty")
    _validate_step(quantity_decimal, quantity_filter.get("stepSize"), "quantity")

    if price_decimal is not None:
        price_filter = get_filter(symbol_info, "PRICE_FILTER")
        _validate_filter_range(price_decimal, price_filter, "price", "minPrice", "maxPrice")
        _validate_step(price_decimal, price_filter.get("tickSize"), "price")

    return {
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "quantity": quantity_decimal,
        "price": price_decimal,
    }


def normalize_choice(value: str, allowed: set[str], field_name: str) -> str:
    normalized = str(value).strip().upper()
    if normalized not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise ValidationError(f"{field_name} must be one of: {allowed_values}.")
    return normalized


def parse_positive_decimal(value: str, field_name: str) -> Decimal:
    try:
        decimal_value = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(f"{field_name} must be a valid decimal number.") from exc

    if decimal_value <= 0:
        raise ValidationError(f"{field_name} must be greater than 0.")

    return decimal_value


def get_filter(symbol_info: dict[str, Any], filter_type: str) -> dict[str, Any]:
    for item in symbol_info.get("filters", []):
        if item.get("filterType") == filter_type:
            return item
    return {}


def _get_quantity_filter(symbol_info: dict[str, Any], order_type: str) -> dict[str, Any]:
    if order_type == "MARKET":
        market_filter = get_filter(symbol_info, "MARKET_LOT_SIZE")
        if market_filter:
            return market_filter
    return get_filter(symbol_info, "LOT_SIZE")


def _validate_filter_range(
    value: Decimal,
    filter_values: dict[str, Any],
    field_name: str,
    min_key: str,
    max_key: str,
) -> None:
    min_value = _decimal_or_none(filter_values.get(min_key))
    max_value = _decimal_or_none(filter_values.get(max_key))

    if min_value is not None and value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}.")

    if max_value is not None and max_value != 0 and value > max_value:
        raise ValidationError(f"{field_name} must be at most {max_value}.")


def _validate_step(value: Decimal, step_value: Any, field_name: str) -> None:
    step = _decimal_or_none(step_value)
    if step is None or step == 0:
        return

    quotient = value / step
    if quotient != quotient.to_integral_value():
        raise ValidationError(f"{field_name} must align with step size {step}.")


def _decimal_or_none(value: Any) -> Decimal | None:
    if value in (None, "", "0", 0):
        return None if value in (None, "") else Decimal("0")
    return Decimal(str(value))
