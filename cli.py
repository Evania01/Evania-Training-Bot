"""CLI entry point for placing Binance Futures testnet orders."""

from __future__ import annotations

import argparse
import sys

from bot.client import BinanceFuturesClient
from bot.exceptions import ApiError, ConfigurationError, NetworkError, ValidationError
from bot.logging_config import configure_logging
from bot.orders import OrderService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Place MARKET or LIMIT orders on Binance Futures Testnet (USDT-M)."
    )
    parser.add_argument("--symbol", required=True, help="Trading pair symbol, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, help="Order side: BUY or SELL")
    parser.add_argument("--type", required=True, help="Order type: MARKET or LIMIT")
    parser.add_argument("--quantity", required=True, help="Order quantity")
    parser.add_argument("--price", help="Limit price. Required only for LIMIT orders")
    parser.add_argument(
        "--log-file",
        default="logs/trading_bot.log",
        help="Path to the application log file",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Optional env file containing BINANCE_API_KEY/BINANCE_API_SECRET",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logger = configure_logging(args.log_file)

    try:
        client = BinanceFuturesClient(logger=logger, env_file=args.env_file)
        client.validate_credentials()
        service = OrderService(client)
        result = service.place_order(
            symbol=args.symbol,
            side=args.side,
            order_type=args.type,
            quantity=args.quantity,
            price=args.price,
        )
    except ConfigurationError as exc:
        logger.error("configuration_error error=%s", exc)
        print(f"Failure: {exc}", file=sys.stderr)
        return 1
    except ValidationError as exc:
        logger.error("validation_error error=%s", exc)
        print(f"Failure: {exc}", file=sys.stderr)
        return 2
    except ApiError as exc:
        logger.error("api_error error=%s body=%s", exc, exc.response_body)
        print(f"Failure: {exc}", file=sys.stderr)
        return 3
    except NetworkError as exc:
        logger.error("network_error error=%s", exc)
        print(f"Failure: {exc}", file=sys.stderr)
        return 4

    _print_request_summary(result["request"])
    _print_response_summary(result["response"])
    print("Success: order submitted to Binance Futures Testnet.")
    return 0


def _print_request_summary(request_data: dict[str, str | None]) -> None:
    print("Order Request Summary")
    print(f"  Symbol: {request_data['symbol']}")
    print(f"  Side: {request_data['side']}")
    print(f"  Type: {request_data['type']}")
    print(f"  Quantity: {request_data['quantity']}")
    if request_data["price"] is not None:
        print(f"  Price: {request_data['price']}")


def _print_response_summary(response_data: dict[str, str | int | None]) -> None:
    print("Order Response Details")
    print(f"  Order ID: {response_data['orderId']}")
    print(f"  Status: {response_data['status']}")
    print(f"  Executed Quantity: {response_data['executedQty']}")
    print(f"  Average Price: {response_data['avgPrice']}")


if __name__ == "__main__":
    raise SystemExit(main())
