"""Config flow for CSNet Home configuration when installing the module via the interface."""

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_ENABLE_ALARM_NOTIFICATIONS,
    CONF_ENERGY_METER,
    CONF_FAN_COIL_MODEL,
    CONF_FILTERED_ALARM_CODES,
    CONF_LANGUAGE,
    CONF_MAX_TEMP_OVERRIDE,
    CONF_POWER_SUPPLY,
    DEFAULT_ENABLE_ALARM_NOTIFICATIONS,
    DEFAULT_FAN_COIL_MODEL,
    DEFAULT_FILTERED_ALARM_CODES,
    DEFAULT_LANGUAGE,
    DEFAULT_POWER_SUPPLY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    FAN_COIL_MODEL_LEGACY,
    FAN_COIL_MODEL_STANDARD,
    MIN_SCAN_INTERVAL,
    POWER_SUPPLY_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL_SCHEMA = vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL))
# Masked in the browser, and never pre-filled: the stored password is not sent to the frontend
# Any energy sensor, from any integration: the integration only reads its state
ENERGY_METER_SELECTOR = EntitySelector(EntitySelectorConfig(domain="sensor", device_class="energy"))
PASSWORD_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD, autocomplete="current-password"))


def _settings_schema(current: dict) -> dict:
    """Return the form fields other than the credentials, pre-filled from the current settings."""
    max_temp_key = vol.Optional(CONF_MAX_TEMP_OVERRIDE)
    if current.get(CONF_MAX_TEMP_OVERRIDE) is not None:
        # a suggestion, not a default: emptying the field removes the override
        max_temp_key = vol.Optional(CONF_MAX_TEMP_OVERRIDE, description={"suggested_value": current[CONF_MAX_TEMP_OVERRIDE]})
    energy_meter_key = vol.Optional(CONF_ENERGY_METER)
    if current.get(CONF_ENERGY_METER):
        energy_meter_key = vol.Optional(CONF_ENERGY_METER, description={"suggested_value": current[CONF_ENERGY_METER]})
    return {
        vol.Optional(
            CONF_SCAN_INTERVAL,
            default=max(current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL), MIN_SCAN_INTERVAL),
        ): SCAN_INTERVAL_SCHEMA,
        vol.Optional(CONF_LANGUAGE, default=current.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)): vol.In(["en", "fr", "es"]),
        max_temp_key: vol.All(vol.Coerce(int), vol.Range(min=8, max=80)),
        vol.Optional(CONF_FAN_COIL_MODEL, default=current.get(CONF_FAN_COIL_MODEL, DEFAULT_FAN_COIL_MODEL)): vol.In(
            [FAN_COIL_MODEL_STANDARD, FAN_COIL_MODEL_LEGACY]
        ),
        vol.Optional(
            CONF_ENABLE_ALARM_NOTIFICATIONS,
            default=current.get(CONF_ENABLE_ALARM_NOTIFICATIONS, DEFAULT_ENABLE_ALARM_NOTIFICATIONS),
        ): bool,
        # a suggestion, not a default: emptying the field means "notify every code"
        vol.Optional(
            CONF_FILTERED_ALARM_CODES,
            description={"suggested_value": current.get(CONF_FILTERED_ALARM_CODES, DEFAULT_FILTERED_ALARM_CODES)},
        ): str,
        vol.Optional(CONF_POWER_SUPPLY, default=current.get(CONF_POWER_SUPPLY, DEFAULT_POWER_SUPPLY)): vol.In(POWER_SUPPLY_OPTIONS),
        # optional, and a suggestion so it can be emptied again
        energy_meter_key: ENERGY_METER_SELECTOR,
    }


def _settings_from_input(user_input: dict) -> dict:
    """Return the settings to store from a submitted form."""
    return {
        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
        CONF_LANGUAGE: user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
        CONF_MAX_TEMP_OVERRIDE: user_input.get(CONF_MAX_TEMP_OVERRIDE),
        CONF_FAN_COIL_MODEL: user_input.get(CONF_FAN_COIL_MODEL, DEFAULT_FAN_COIL_MODEL),
        CONF_ENABLE_ALARM_NOTIFICATIONS: user_input.get(CONF_ENABLE_ALARM_NOTIFICATIONS, DEFAULT_ENABLE_ALARM_NOTIFICATIONS),
        # the frontend leaves an emptied field out of what it sends
        CONF_FILTERED_ALARM_CODES: user_input.get(CONF_FILTERED_ALARM_CODES, ""),
        CONF_POWER_SUPPLY: user_input.get(CONF_POWER_SUPPLY, DEFAULT_POWER_SUPPLY),
        # any energy sensor of Home Assistant that measures the heat pump; none by default
        CONF_ENERGY_METER: user_input.get(CONF_ENERGY_METER) or None,
    }


def _settings_errors(user_input: dict) -> dict[str, str]:
    """Return the errors in the submitted settings, by field."""
    codes = user_input.get(CONF_FILTERED_ALARM_CODES) or ""
    try:
        for code in codes.split(","):
            if code.strip():
                int(code.strip())
    except ValueError:
        return {CONF_FILTERED_ALARM_CODES: "invalid_alarm_codes"}
    return {}


class CsnetHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CSNet Home."""

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow: the heating curves of the circuits."""
        return CsnetHomeOptionsFlow()

    async def async_step_user(self, user_input=None):
        """Handle user input for login credentials."""
        errors = {}

        if user_input is not None:
            errors = _settings_errors(user_input)
            if not errors:
                # Validate credentials before creating entry
                errors = await self._validate_credentials(user_input[CONF_USERNAME], user_input[CONF_PASSWORD]) or {}

            if not errors:
                return self.async_create_entry(
                    title="CSNet Home",
                    data={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        **_settings_from_input(user_input),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR,
                **_settings_schema({}),
            }
        )
        return self.async_show_form(
            step_id="user",
            # keep what was typed when the form comes back with an error, except the password
            data_schema=self.add_suggested_values_to_schema(schema, {k: v for k, v in (user_input or {}).items() if k != CONF_PASSWORD}),
            errors=errors,
        )

    async def _validate_credentials(self, username: str, password: str) -> dict[str, str] | None:
        """Validate credentials with the CSNet API.

        Args:
            username: CSNet username
            password: CSNet password

        Returns:
            dict with error key if validation failed, None if successful
        """
        from .api import CSNetHomeAPI

        _LOGGER.debug("Config flow: Validating credentials")
        try:
            # Validate credentials using the API
            is_valid = await CSNetHomeAPI.async_validate_credentials(self.hass, username, password)

            if not is_valid:
                _LOGGER.warning("Config flow: Credential validation returned False")
                return {"base": "invalid_auth"}

            _LOGGER.info("Config flow: Credentials validated successfully")
            return None  # No errors

        except Exception as e:
            _LOGGER.error("Config flow: Error during credential validation: %s", e, exc_info=True)
            return {"base": "cannot_connect"}

    async def async_step_reconfigure(self, user_input=None):
        """Handle reconfiguration of the integration."""
        reconfigure_entry = self._get_reconfigure_entry()
        current = reconfigure_entry.data
        errors = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            # an empty password field keeps the stored password
            password = user_input.get(CONF_PASSWORD) or current.get(CONF_PASSWORD)

            errors = _settings_errors(user_input)
            credentials_changed = username != current.get(CONF_USERNAME) or password != current.get(CONF_PASSWORD)
            if not errors and credentials_changed:
                # Unchanged credentials are in use already: no extra login for a settings change
                errors = await self._validate_credentials(username, password) or {}

            if not errors:
                # Update the config entry with new values and reload
                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    data_updates={
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                        **_settings_from_input(user_input),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME, default=current.get(CONF_USERNAME)): str,
                vol.Optional(CONF_PASSWORD): PASSWORD_SELECTOR,
                **_settings_schema(current),
            }
        )
        if user_input is not None:
            # back with an error: keep what was typed, except the password
            schema = self.add_suggested_values_to_schema(schema, {k: v for k, v in user_input.items() if k != CONF_PASSWORD})
        return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data):
        """Handle reauthentication when credentials are invalid."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Handle reauthentication confirmation."""
        errors = {}
        reauth_entry = self._get_reauth_entry()

        if user_input is not None:
            # Validate new credentials
            errors = await self._validate_credentials(user_input[CONF_USERNAME], user_input[CONF_PASSWORD]) or {}

            if not errors:
                # Update credentials and reload (no update listener: the flow
                # owns the reload, as Home Assistant requires from 2026.12)
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                    reason="reauth_successful",
                )

        # Show form with current username pre-filled
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=reauth_entry.data.get(CONF_USERNAME, "")): str,
                    vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR,
                }
            ),
            errors=errors,
        )


def _number_selector(value_range: tuple[float, float], step: float, unit: str | None = "°C") -> NumberSelector:
    config = NumberSelectorConfig(min=value_range[0], max=value_range[1], step=step, mode=NumberSelectorMode.BOX)
    if unit:
        config["unit_of_measurement"] = unit
    return NumberSelector(config)


def _curve_field_selectors() -> dict:
    """Return the selector of each heating curve field."""
    # imported here: the curve module is only needed by the options flow
    from .heating_curve import (  # pylint: disable=import-outside-toplevel
        AMBIENT_RANGE,
        GRADIENT,
        GRADIENT_RANGE,
        HIGH_AMBIENT,
        LOW_AMBIENT,
        VERTEX_OFFSET,
        VERTEX_OFFSET_RANGE,
        WATER_AT_HIGH_AMBIENT,
        WATER_AT_LOW_AMBIENT,
        WATER_RANGE,
    )

    return {
        LOW_AMBIENT: _number_selector(AMBIENT_RANGE, 1),
        WATER_AT_LOW_AMBIENT: _number_selector(WATER_RANGE, 1),
        HIGH_AMBIENT: _number_selector(AMBIENT_RANGE, 1),
        WATER_AT_HIGH_AMBIENT: _number_selector(WATER_RANGE, 1),
        GRADIENT: _number_selector(GRADIENT_RANGE, 0.1, None),
        VERTEX_OFFSET: _number_selector(VERTEX_OFFSET_RANGE, 1),
    }


def _curve_errors(user_input: dict, circuits: dict[int, int]) -> dict[str, str]:
    """Return the errors in the submitted curves, by field: a curve is complete or empty."""
    from .const import OTC_HEATING_TYPE_POINTS  # pylint: disable=import-outside-toplevel
    from .heating_curve import FIELDS_BY_TYPE, HIGH_AMBIENT, LOW_AMBIENT, option_key  # pylint: disable=import-outside-toplevel

    errors = {}
    for circuit, curve_type in circuits.items():
        keys = [option_key(circuit, field) for field in FIELDS_BY_TYPE[curve_type]]
        missing = [key for key in keys if user_input.get(key) is None]
        if missing and len(missing) < len(keys):
            errors[missing[0]] = "incomplete_curve"
        elif not missing and curve_type == OTC_HEATING_TYPE_POINTS:
            low, high = user_input[option_key(circuit, LOW_AMBIENT)], user_input[option_key(circuit, HIGH_AMBIENT)]
            if low >= high:
                errors[option_key(circuit, HIGH_AMBIENT)] = "high_ambient_not_above_low"
    return errors


# Home Assistant 2025.8 and later reload the entry when the options change; older ones need a manual reload
_OptionsFlowBase = getattr(config_entries, "OptionsFlowWithReload", config_entries.OptionsFlow)


class CsnetHomeOptionsFlow(_OptionsFlowBase):
    """Let the user copy the installer's heating curves, which CSNet does not report.

    Nothing entered here is sent to the unit: it only feeds the heating curve sensors.
    """

    async def async_step_init(self, user_input=None):
        """Ask for the curve of each circuit that uses one, with the fields of the kind of curve it uses."""
        # imported here: the curve module is only needed by the options flow
        from .const import OTC_HEATING_TYPE_NAMES  # pylint: disable=import-outside-toplevel
        from .heating_curve import FIELDS_BY_TYPE, VERTEX_OFFSET, curve_circuits, option_key  # pylint: disable=import-outside-toplevel
        from .sensor import _get_heating_status_from_installation_data  # pylint: disable=import-outside-toplevel

        runtime_data = getattr(self.config_entry, "runtime_data", None)
        coordinator = getattr(runtime_data, "coordinator", None)
        if coordinator is None:
            return self.async_abort(reason="not_loaded")
        status = _get_heating_status_from_installation_data(coordinator.get_installation_devices_data())
        zone_ids = {sensor.get("zone_id") for sensor in coordinator.get_sensors_data()}
        circuits = curve_circuits(status, zone_ids)
        if not circuits:
            return self.async_abort(reason="no_heating_curve")

        current = dict(self.config_entry.options)
        errors = {}
        if user_input is not None:
            errors = _curve_errors(user_input, circuits)
            if not errors:
                options = dict(current)
                for circuit, curve_type in circuits.items():
                    for field in (*FIELDS_BY_TYPE[curve_type], VERTEX_OFFSET):
                        key = option_key(circuit, field)
                        # the frontend leaves an emptied field out of what it sends
                        if user_input.get(key) is None:
                            options.pop(key, None)
                        else:
                            options[key] = float(user_input[key])
                return self.async_create_entry(data=options)

        selectors = _curve_field_selectors()
        fields = {}
        for circuit, curve_type in circuits.items():
            for field in (*FIELDS_BY_TYPE[curve_type], VERTEX_OFFSET):
                fields[vol.Optional(option_key(circuit, field))] = selectors[field]
        schema = self.add_suggested_values_to_schema(vol.Schema(fields), user_input if user_input is not None else current)
        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "circuits": ", ".join(f"C{circuit}: {OTC_HEATING_TYPE_NAMES[curve_type]}" for circuit, curve_type in circuits.items()),
            },
        )
