"""Tests for the ASIC Miner data coordinator."""

import unittest
from unittest.mock import AsyncMock, Mock, patch

from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.asic_miner.coordinator import MinerCoordinator


def _coordinator_with_miner(miner) -> MinerCoordinator:
    """Create a coordinator focused on update behavior."""
    coordinator = MinerCoordinator.__new__(MinerCoordinator)
    coordinator.ip = "192.168.1.10"
    coordinator.username = None
    coordinator.password = None
    coordinator.miner = miner
    return coordinator


class MinerCoordinatorTest(unittest.IsolatedAsyncioTestCase):
    """Verify coordinator reconnection behavior."""

    async def test_revalidates_existing_miner_before_polling(self) -> None:
        """The existing miner is revalidated before its data is requested."""
        data = object()
        miner = AsyncMock()
        miner.revalidate.return_value = True
        miner.get_data.return_value = data
        coordinator = _coordinator_with_miner(miner)

        self.assertIs(await coordinator._async_update_data(), data)
        miner.revalidate.assert_awaited_once_with()
        miner.get_data.assert_awaited_once_with()

    @patch("custom_components.asic_miner.coordinator.MinerFactory")
    async def test_replaces_miner_when_revalidation_fails(
        self, factory_cls: Mock
    ) -> None:
        """A failed revalidation triggers miner rediscovery."""
        data = object()
        old_miner = AsyncMock()
        old_miner.revalidate.return_value = False
        new_miner = AsyncMock()
        new_miner.revalidate.return_value = True
        new_miner.get_data.return_value = data
        factory_cls.return_value.get_miner = AsyncMock(return_value=new_miner)
        coordinator = _coordinator_with_miner(old_miner)

        self.assertIs(await coordinator._async_update_data(), data)

        old_miner.revalidate.assert_awaited_once_with()
        old_miner.get_data.assert_not_awaited()
        factory_cls.return_value.get_miner.assert_awaited_once_with(coordinator.ip)
        self.assertIs(coordinator.miner, new_miner)
        new_miner.revalidate.assert_awaited_once_with()
        new_miner.get_data.assert_awaited_once_with()

    @patch("custom_components.asic_miner.coordinator.MinerFactory")
    async def test_clears_miner_when_rediscovery_returns_none(
        self, factory_cls: Mock
    ) -> None:
        """An unidentified miner raises UpdateFailed so entities become unavailable."""
        miner = AsyncMock()
        miner.revalidate.return_value = False
        factory_cls.return_value.get_miner = AsyncMock(return_value=None)
        coordinator = _coordinator_with_miner(miner)

        with self.assertRaisesRegex(UpdateFailed, "Could not identify miner"):
            await coordinator._async_update_data()

        self.assertIsNone(coordinator.miner)

    @patch("custom_components.asic_miner.coordinator.MinerFactory")
    async def test_invalid_rediscovered_miner_marks_coordinator_unavailable(
        self, factory_cls: Mock
    ) -> None:
        """A rediscovered miner must pass revalidation before it is polled."""
        miner = AsyncMock()
        miner.revalidate.return_value = False
        replacement = AsyncMock()
        replacement.revalidate.return_value = False
        factory_cls.return_value.get_miner = AsyncMock(return_value=replacement)
        coordinator = _coordinator_with_miner(miner)

        with self.assertRaisesRegex(UpdateFailed, "Could not validate miner"):
            await coordinator._async_update_data()

        self.assertIsNone(coordinator.miner)
        replacement.get_data.assert_not_awaited()
