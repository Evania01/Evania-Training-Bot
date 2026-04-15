"""Unit tests for validation helpers."""

from __future__ import annotations

import unittest
from decimal import Decimal

from bot.exceptions import ValidationError
from bot.validators import validate_order_inputs


def build_symbol_info() -> dict[str, object]:
    return {
        "symbol": "BTCUSDT",
        "status": "TRADING",
        "quoteAsset": "USDT",
        "marginAsset": "USDT",
        "filters": [
            {
                "filterType": "LOT_SIZE",
                "minQty": "0.001",
                "maxQty": "1000",
                "stepSize": "0.001",
            },
            {
                "filterType": "MARKET_LOT_SIZE",
                "minQty": "0.001",
                "maxQty": "1000",
                "stepSize": "0.001",
            },
            {
                "filterType": "PRICE_FILTER",
                "minPrice": "0.10",
                "maxPrice": "1000000",
                "tickSize": "0.10",
            },
        ],
    }


class ValidateOrderInputsTests(unittest.TestCase):
    def test_accepts_valid_market_order(self) -> None:
        result = validate_order_inputs(
            symbol_info=build_symbol_info(),
            side="buy",
            order_type="market",
            quantity="0.005",
            price=None,
        )

        self.assertEqual(result["symbol"], "BTCUSDT")
        self.assertEqual(result["side"], "BUY")
        self.assertEqual(result["order_type"], "MARKET")
        self.assertEqual(result["quantity"], Decimal("0.005"))
        self.assertIsNone(result["price"])

    def test_accepts_valid_limit_order(self) -> None:
        result = validate_order_inputs(
            symbol_info=build_symbol_info(),
            side="SELL",
            order_type="LIMIT",
            quantity="0.010",
            price="70000.10",
        )

        self.assertEqual(result["price"], Decimal("70000.10"))

    def test_rejects_missing_price_for_limit_order(self) -> None:
        with self.assertRaisesRegex(ValidationError, "price is required"):
            validate_order_inputs(
                symbol_info=build_symbol_info(),
                side="SELL",
                order_type="LIMIT",
                quantity="0.010",
            )

    def test_rejects_price_for_market_order(self) -> None:
        with self.assertRaisesRegex(ValidationError, "must not be supplied"):
            validate_order_inputs(
                symbol_info=build_symbol_info(),
                side="BUY",
                order_type="MARKET",
                quantity="0.010",
                price="70000",
            )

    def test_rejects_non_positive_quantity(self) -> None:
        with self.assertRaisesRegex(ValidationError, "quantity must be greater than 0"):
            validate_order_inputs(
                symbol_info=build_symbol_info(),
                side="BUY",
                order_type="MARKET",
                quantity="0",
            )

    def test_rejects_invalid_side(self) -> None:
        with self.assertRaisesRegex(ValidationError, "side must be one of"):
            validate_order_inputs(
                symbol_info=build_symbol_info(),
                side="HOLD",
                order_type="MARKET",
                quantity="0.010",
            )

    def test_rejects_unknown_symbol(self) -> None:
        with self.assertRaisesRegex(ValidationError, "Symbol is not available"):
            validate_order_inputs(
                symbol_info=None,
                side="BUY",
                order_type="MARKET",
                quantity="0.010",
            )

    def test_rejects_bad_quantity_step_size(self) -> None:
        with self.assertRaisesRegex(ValidationError, "quantity must align"):
            validate_order_inputs(
                symbol_info=build_symbol_info(),
                side="BUY",
                order_type="MARKET",
                quantity="0.0015",
            )

    def test_rejects_bad_price_tick_size(self) -> None:
        with self.assertRaisesRegex(ValidationError, "price must align"):
            validate_order_inputs(
                symbol_info=build_symbol_info(),
                side="SELL",
                order_type="LIMIT",
                quantity="0.010",
                price="70000.15",
            )


if __name__ == "__main__":
    unittest.main()
