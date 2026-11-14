# Dashboard Cards

The integration ships six dashboard cards. You don't need to install anything else: no HACS frontend download and no third-party card. After the integration is set up (and the browser page is reloaded once), the cards appear in the dashboard **Add card** picker. Search for **CSNet**.

The cards find their entities themselves, so a card works as soon as you add it, even if you renamed the entities or use Home Assistant in another language. They follow your theme (light and dark) and are translated to English, French and Spanish.

| Card | Type | What it shows |
|------|------|---------------|
| Heat pump | `custom:csnet-heat-pump-card` | Power gauge with a spinning fan while the compressor runs, the unit's status, compressor frequency, outdoor temperature, water ΔT, today's electricity, heat and COP |
| Water circuit | `custom:csnet-water-circuit-card` | Live diagram: outdoor unit, flow and return temperatures, each circuit with its room temperature, setpoint and demand, the mixing valve of circuit 2, the hot water tank and pool when present, pumps, flow rate and pressure |
| Heating curve | `custom:csnet-heating-curve-card` | The heating curves you entered in the integration options, where the unit is on them now, and the unit's water target over the last days |
| Performance | `custom:csnet-performance-card` | COP now, today, yesterday, this month and last month, with the share of heat taken from the air |
| System health | `custom:csnet-system-health-card` | Alarms, gateway, central control, defrost and water pressure |
| Refrigerant circuit | `custom:csnet-refrigerant-card` | Compressor frequency and current, discharge, evaporator, gas and liquid temperatures, pressures, expansion valve, outdoor fan |

Tap any value to open its entity's details.

## A ready-made view

Paste this into a new view (dashboard → edit → ⋮ → Raw configuration editor) to get all six cards:

```yaml
title: Heat pump
path: heat-pump
type: sections
max_columns: 4
sections:
  - type: grid
    cards:
      - type: custom:csnet-heat-pump-card
      - type: custom:csnet-performance-card
  - type: grid
    column_span: 2
    cards:
      - type: custom:csnet-water-circuit-card
      - type: custom:csnet-heating-curve-card
  - type: grid
    cards:
      - type: custom:csnet-system-health-card
      - type: custom:csnet-refrigerant-card
```

## Options

Every card accepts `title` (an empty title hides it). Some cards have more options, also available in the visual editor:

| Card | Option | Meaning |
|------|--------|---------|
| Heat pump | `power_entity` | A power sensor (W) to use instead of the integration's estimate, for example a real electricity meter on the heat pump's circuit |
| Heat pump | `max_power` | Value of a full gauge, in W (default 4000) |
| Heating curve | `days` | Days of history drawn as dots (default 7, 0 for none) |
| System health | `pressure_min`, `pressure_max` | Normal water pressure range of your installation, in bar. Outside it, the pressure is flagged. Without them the pressure is only shown |

Any entity a card uses can be replaced with `<role>_entity`, for example `outdoor_entity: sensor.my_weather_station`. The roles:

| Role | Entity |
|------|--------|
| `power`, `heat_power`, `cop_now` | Instant consumption, output power, instant COP |
| `energy_today`, `heat_today` | Daily consumption and heat (estimated) |
| `server_heat_today` / `_yesterday` / `_month`, `server_electricity_*` | Energy recorded by CSNet |
| `cop_today`, `cop_yesterday`, `cop_month`, `cop_last_month` | COP from your electricity meter |
| `water_out`, `water_in`, `water_target`, `water_c2`, `water_flow`, `water_pressure`, `mix_valve` | Water side |
| `outdoor`, `outdoor_average` | Outdoor temperature, and the average the unit uses for its curves |
| `compressor`, `defrost`, `pump_1`, `pump_2`, `pump_3`, `backup_heater`, `boiler` | What runs |
| `compressor_frequency`, `compressor_current`, `discharge_temperature`, `evaporator_temperature`, `gas_temperature`, `liquid_temperature`, `discharge_pressure`, `suction_pressure`, `expansion_valve`, `outdoor_fan_rpm` | Refrigerant circuit |

## Heating curve card

The lines are drawn from the curve values you enter in **Settings → Devices & services → CSNet Home → Configure** (see [Heating Curve Values](Advanced-Features.md#heating-curve-values-water-law)). Without them the card still shows the unit's water target and its history, with a reminder to enter the curves.

The dots are the unit's water target, averaged per hour, against the average outdoor temperature, from Home Assistant's long-term statistics. Darker dots are the last 24 hours. When the dots sit above the line, the unit is adding room compensation; below, it is in eco mode or the line does not match the unit's settings.

## Performance card

The COP needs an electricity figure. With an electricity meter chosen in the integration settings (Reconfigure → Electricity meter of the heat pump), the card shows the metered COP. Without one, it uses the electricity CSNet records when your unit has a pulse meter; otherwise it shows the heat produced only.

## Troubleshooting

- **The cards are not in the picker**: reload the browser page (the card file is loaded when the page opens). On the companion app, pull down to refresh or clear the frontend cache.
- **"CSNet Home is not set up, or this browser loaded an older version"**: the integration is not loaded, or the browser still runs a cached page from before the update. Reload the page.
- **A value shows "–"**: the unit does not report it, or the entity is disabled. Enable the entity, or replace it with `<role>_entity`.
