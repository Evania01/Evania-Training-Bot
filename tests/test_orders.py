"""Unit tests for the order service."""

from __future__ import annotations

import unittest
from unittest.mock import Mock

from bot.exceptions import ApiError, NetworkError
from bot.orders import OrderService


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


class OrderServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = Mock()
        self.client.get_symbol_info.return_value = build_symbol_info()
        self.service = OrderService(self.client)

    def test_places_market_order(self) -> None:
        self.client.create_order.return_value = {
            "symbol": "BTCUSDT",
            "orderId": 12345,
            "status": "FILLED",
            "executedQty": "0.005",
            "avgPrice": "68000.50",
            "price": "0",
            "side": "BUY",
            "type": "MARKET",
        }

        result = self.service.place_order("btcusdt", "buy", "market", "0.005")

        self.client.create_order.assert_called_once_with(
            {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "MARKET",
                "quantity": "0.005",
                "newOrderRespType": "RESULT",
            }
        )
        self.client.query_order.assert_not_called()
        self.assertEqual(result["response"]["orderId"], 12345)
        self.assertEqual(result["response"]["status"], "FILLED")
        self.assertEqual(result["response"]["avgPrice"], "68000.50")

    def test_places_limit_order(self) -> None:
        self.client.create_order.return_value = {
            "symbol": "BTCUSDT",
            "orderId": 22222,
            "status": "NEW",
            "executedQty": "0",
            "avgPrice": "0.0",
            "price": "70000.10",
            "side": "SELL",
            "type": "LIMIT",
        }

        self.service.place_order("BTCUSDT", "SELL", "LIMIT", "0.010", "70000.10")

        self.client.create_order.assert_called_once_with(
            {
                "symbol": "BTCUSDT",
                "side": "SELL",
                "type": "LIMIT",
                "quantity": "0.01",
                "newOrderRespType": "RESULT",
                "price": "70000.1",
                "timeInForce": "GTC",
            }
        )

    def test_enriches_response_when_fields_are_missing(self) -> None:
        self.client.create_order.return_value = {
            "symbol": "BTCUSDT",
            "orderId": 99999,
            "side": "BUY",
            "type": "MARKET",
        }
        self.client.query_order.return_value = {
            "symbol": "BTCUSDT",
            "orderId": 99999,
            "status": "FILLED",
            "executedQty": "0.010",
            "avgPrice": "68100.00",
            "price": "0",
            "side": "BUY",
            "type": "MARKET",
        }

        result = self.service.place_order("BTCUSDT", "BUY", "MARKET", "0.010")

        self.client.query_order.assert_called_once_with("BTCUSDT", 99999)
        self.assertEqual(result["response"]["status"], "FILLED")
        self.assertEqual(result["response"]["executedQty"], "0.010")
        self.assertEqual(result["response"]["avgPrice"], "68100.00")

    def test_surfaces_api_errors(self) -> None:
        self.client.create_order.side_effect = ApiError(400, -1013, "Invalid quantity")

        with self.assertRaises(ApiError):
            self.service.place_order("BTCUSDT", "BUY", "MARKET", "0.010")

    def test_surfaces_network_errors(self) -> None:
        self.client.create_order.side_effect = NetworkError("Timeout")

        with self.assertRaises(NetworkError):
            self.service.place_order("BTCUSDT", "BUY", "MARKET", "0.010")


if __name__ == "__main__":
    unittest.main()
