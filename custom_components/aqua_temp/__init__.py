import logging
import sys

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .common.consts import DOMAIN
from .common.entity_descriptions import ALL_ENTITIES
from .common.exceptions import LoginError
from .managers.aqua_temp_api import AquaTempAPI
from .managers.aqua_temp_config_manager import AquaTempConfigManager
from .managers.aqua_temp_coordinator import AquaTempCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Shinobi Video component."""
    initialized = False

    try:
        platforms = _get_platforms()

        config_manager = AquaTempConfigManager(hass, entry)
        await config_manager.initialize()

        api = AquaTempAPI(hass, config_manager)
        await api.initialize()

        coordinator = AquaTempCoordinator(hass, api, config_manager)

        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

        await hass.config_entries.async_forward_entry_setups(entry, platforms)

        _LOGGER.info(f"Start loading {DOMAIN} integration, Entry ID: {entry.entry_id}")

        await coordinator.async_config_entry_first_refresh()

        _LOGGER.info("Finished loading integration")

        initialized = True

    except LoginError:
        _LOGGER.info("Failed to login Aqua Temp API, cannot log integration")

    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(f"Failed to load Aqua Temp, error: {ex}, line: {line_number}")

    return initialized


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.info(f"Unloading {DOMAIN} integration, Entry ID: {entry.entry_id}")

    platforms = _get_platforms()

    for platform in platforms:
        await hass.config_entries.async_forward_entry_unload(entry, platform)

    del hass.data[DOMAIN][entry.entry_id]

    return True


def _get_platforms():
    platforms = []
    for entity_description in ALL_ENTITIES:
        if (
            entity_description.platform not in platforms
            and entity_description.platform is not None
        ):
            platforms.append(entity_description.platform)

    return platforms
