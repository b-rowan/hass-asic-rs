"""Tests for ASIC miner network discovery."""

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from homeassistant import config_entries
from homeassistant.const import CONF_HOST

from custom_components.asic_miner.config_flow import AsicMinerConfigFlow
from custom_components.asic_miner.const import DOMAIN
from custom_components.asic_miner.discovery import (
    DISCOVERY_CONCURRENCY,
    async_default_subnet,
    async_discover_miners,
    async_scan_subnet,
)


class _ScanStream:
    """Async iterator containing scan results."""

    def __init__(self, results) -> None:
        self._results = iter(results)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._results)
        except StopIteration:
            raise StopAsyncIteration from None


class DiscoveryTest(unittest.IsolatedAsyncioTestCase):
    """Verify local network discovery behavior."""

    @patch("custom_components.asic_miner.discovery.async_get_adapters")
    async def test_uses_default_adapter_subnet(self, get_adapters: AsyncMock) -> None:
        """Discovery derives the scan range from the default HA adapter."""
        get_adapters.return_value = [
            {
                "default": True,
                "ipv4": [{"address": "192.168.20.42", "network_prefix": 24}],
            }
        ]

        self.assertEqual(await async_default_subnet(Mock()), "192.168.20.0/24")

    @patch("custom_components.asic_miner.discovery.MinerFactory")
    async def test_scan_returns_only_supported_miners(self, factory_cls: Mock) -> None:
        """Unsupported addresses are omitted from scan results."""
        miner = SimpleNamespace(make="Bitaxe", model="Gamma")
        configured_factory = factory_cls.from_subnet.return_value
        factory = configured_factory.with_concurrent_limit.return_value
        factory.scan_stream_with_ip.return_value = _ScanStream(
            [("192.168.20.10", miner), ("192.168.20.11", None)]
        )

        self.assertEqual(
            await async_scan_subnet("192.168.20.0/24"),
            {"192.168.20.10": "Bitaxe Gamma (192.168.20.10)"},
        )
        configured_factory.with_concurrent_limit.assert_called_once_with(
            DISCOVERY_CONCURRENCY
        )

    @patch("custom_components.asic_miner.discovery.async_scan_subnet")
    @patch("custom_components.asic_miner.discovery.async_default_subnet")
    async def test_starts_flow_only_for_unconfigured_miners(
        self, default_subnet: AsyncMock, scan_subnet: AsyncMock
    ) -> None:
        """Automatic scans create discovery flows without duplicating entries."""
        default_subnet.return_value = "192.168.20.0/24"
        scan_subnet.return_value = {
            "192.168.20.10": "Bitaxe Gamma (192.168.20.10)",
            "192.168.20.11": "Antminer S19 (192.168.20.11)",
        }
        hass = Mock()
        hass.config_entries.async_entries.return_value = [
            SimpleNamespace(data={CONF_HOST: "192.168.20.10"})
        ]
        hass.config_entries.flow.async_init = AsyncMock()

        await async_discover_miners(hass)

        hass.config_entries.flow.async_init.assert_awaited_once_with(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data={
                CONF_HOST: "192.168.20.11",
                "title": "Antminer S19 (192.168.20.11)",
            },
        )

    async def test_discovered_miner_requires_user_confirmation(self) -> None:
        """A discovery continues to credentials instead of creating an entry."""
        flow = AsicMinerConfigFlow()
        flow.context = {"source": config_entries.SOURCE_INTEGRATION_DISCOVERY}
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = Mock()
        expected_result = {"type": "form", "step_id": "credentials"}
        flow.async_step_credentials = AsyncMock(return_value=expected_result)

        result = await flow.async_step_integration_discovery(
            {
                CONF_HOST: "192.168.20.11",
                "title": "Antminer S19 (192.168.20.11)",
            }
        )

        self.assertIs(result, expected_result)
        flow.async_set_unique_id.assert_awaited_once_with("192.168.20.11")
        flow._abort_if_unique_id_configured.assert_called_once_with()
        flow.async_step_credentials.assert_awaited_once_with()
