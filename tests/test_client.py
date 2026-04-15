"""Unit tests for client configuration helpers."""

from __future__ import annotations

import os
import tempfile
import unittest

from bot.client import BinanceFuturesClient, load_env_file


class ClientConfigurationTests(unittest.TestCase):
    def test_load_env_file_sets_missing_values(self) -> None:
        original_key = os.environ.pop("BINANCE_API_KEY", None)
        original_secret = os.environ.pop("BINANCE_API_SECRET", None)
        original_base_url = os.environ.pop("BINANCE_BASE_URL", None)

        try:
            with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
                tmp.write("BINANCE_API_KEY=test-key\n")
                tmp.write("BINANCE_API_SECRET=test-secret\n")
                tmp.write("BINANCE_BASE_URL=https://example.test\n")
                env_path = tmp.name

            load_env_file(env_path)

            self.assertEqual(os.environ["BINANCE_API_KEY"], "test-key")
            self.assertEqual(os.environ["BINANCE_API_SECRET"], "test-secret")
            self.assertEqual(os.environ["BINANCE_BASE_URL"], "https://example.test")
        finally:
            if original_key is None:
                os.environ.pop("BINANCE_API_KEY", None)
            else:
                os.environ["BINANCE_API_KEY"] = original_key

            if original_secret is None:
                os.environ.pop("BINANCE_API_SECRET", None)
            else:
                os.environ["BINANCE_API_SECRET"] = original_secret

            if original_base_url is None:
                os.environ.pop("BINANCE_BASE_URL", None)
            else:
                os.environ["BINANCE_BASE_URL"] = original_base_url

            os.unlink(env_path)

    def test_client_reads_values_from_env_file(self) -> None:
        original_key = os.environ.pop("BINANCE_API_KEY", None)
        original_secret = os.environ.pop("BINANCE_API_SECRET", None)

        try:
            with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
                tmp.write("BINANCE_API_KEY=file-key\n")
                tmp.write("BINANCE_API_SECRET=file-secret\n")
                env_path = tmp.name

            client = BinanceFuturesClient(env_file=env_path)

            self.assertEqual(client.api_key, "file-key")
            self.assertEqual(client.api_secret, "file-secret")
        finally:
            if original_key is None:
                os.environ.pop("BINANCE_API_KEY", None)
            else:
                os.environ["BINANCE_API_KEY"] = original_key

            if original_secret is None:
                os.environ.pop("BINANCE_API_SECRET", None)
            else:
                os.environ["BINANCE_API_SECRET"] = original_secret

            os.unlink(env_path)


if __name__ == "__main__":
    unittest.main()
