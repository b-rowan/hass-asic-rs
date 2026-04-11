"""Config flow for ASIC Miner integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from pyasic_rs import MinerFactory

from .const import DOMAIN

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_USERNAME, default=""): str,
        vol.Optional(CONF_PASSWORD, default=""): str,
    }
)


async def _validate_and_get_title(hass: HomeAssistant, data: dict) -> str:
    """Connect to the miner and return a display title, or raise on failure."""
    factory = MinerFactory()
    miner = await factory.get_miner(data[CONF_HOST])
    if miner is None:
        raise ConnectionError("cannot_connect")

    username = data.get(CONF_USERNAME) or ""
    password = data.get(CONF_PASSWORD) or ""
    if username and password:
        miner.set_auth(username, password)

    miner_data = await miner.get_data()
    make = miner_data.device_info.make
    model = miner_data.device_info.model
    return f"{make} {model} ({data[CONF_HOST]})"


class AsicMinerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ASIC Miner."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                title = await _validate_and_get_title(self.hass, user_input)
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                # Strip empty credential strings before storing
                data = {CONF_HOST: user_input[CONF_HOST]}
                if user_input.get(CONF_USERNAME):
                    data[CONF_USERNAME] = user_input[CONF_USERNAME]
                if user_input.get(CONF_PASSWORD):
                    data[CONF_PASSWORD] = user_input[CONF_PASSWORD]

                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=title, data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )
