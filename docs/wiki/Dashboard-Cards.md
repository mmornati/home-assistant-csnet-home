# Dashboard Cards

The integration ships eleven dashboard cards. You don't need to install anything else: no HACS frontend download and no third-party card. After the integration is set up (and the browser page is reloaded once), the cards appear in the dashboard **Add card** picker. Search for **CSNet**.

The cards find their entities themselves, so a card works as soon as you add it, even if you renamed the entities or use Home Assistant in another language. They follow your theme (light and dark) and are translated to English, French and Spanish: by default in each user's profile language, or in the **Card language** chosen in the integration settings.

| Card | Type | What it shows |
|------|------|---------------|
| Heat pump | `custom:csnet-heat-pump-card` | Power gauge with a spinning fan while the compressor runs, the unit's status, compressor frequency, outdoor temperature, water ΔT, today's electricity, heat and COP |
| Water circuit | `custom:csnet-water-circuit-card` | Live diagram: outdoor unit, flow and return temperatures, each circuit with its room temperature, setpoint and demand, the mixing valve of circuit 2, the hot water tank and pool when present, pumps, flow rate and pressure |
| Heating curve | `custom:csnet-heating-curve-card` | The heating curves you entered in the integration options, where the unit is on them now, and the unit's water target over the last days |
| Performance | `custom:csnet-performance-card` | COP now, today, yesterday, this month and last month, with the share of heat taken from the air |
| System health | `custom:csnet-system-health-card` | Alarms, gateway, central control, defrost and water pressure |
| Refrigerant circuit | `custom:csnet-refrigerant-card` | Compressor frequency and current, discharge, evaporator, gas and liquid temperatures, pressures, expansion valve, outdoor fan |
| Temperatures | `custom:csnet-temperatures-card` | Flow, return, after the mixing valve, water target and outdoor temperature over the last hours, with the compressor frequency behind |
| Activity | `custom:csnet-activity-card` | What ran over the last hours, with the total time: compressor, defrost, each circuit's demand, hot water, pumps, backup heater, boiler |
| Energy per day | `custom:csnet-daily-energy-card` | Electricity and heat per day, the COP of each day and the average outdoor temperature |
| Power today | `custom:csnet-power-profile-card` | Today's power against the average day of the last two weeks |
| Energy signature | `custom:csnet-energy-signature-card` | Tomorrow's electricity from the weather forecast, kWh per degree colder, 7-day average and base load |

Tap any value to open its entity's details.

<div class="csnet-video" markdown>
<iframe src="../../videos/csnet-home-tour/?embed=1&lang=en" title="A one-minute narrated tour of the integration" loading="lazy" allow="fullscreen; autoplay" allowfullscreen></iframe>
</div>

*A one-minute narrated tour ([version française](../../videos/csnet-home-tour/?lang=fr)).*

![A heat pump view built only from the bundled cards](../images/cards/board-light.jpg#only-light){ loading=lazy }
![A heat pump view built only from the bundled cards](../images/cards/board-dark.jpg#only-dark){ loading=lazy }

*A view made only of the bundled cards, on a Yutaki S with two circuits (test instance, two days of history).*

## The cards

### Heat pump

![Heat pump card](../images/cards/card-heat-pump-light.jpg#only-light){ loading=lazy width="560" }
![Heat pump card](../images/cards/card-heat-pump-dark.jpg#only-dark){ loading=lazy width="560" }

### Water circuit

![Water circuit card](../images/cards/card-water-circuit-light.jpg#only-light){ loading=lazy width="560" }
![Water circuit card](../images/cards/card-water-circuit-dark.jpg#only-dark){ loading=lazy width="560" }

### Heating curve

![Heating curve card](../images/cards/card-heating-curve-light.jpg#only-light){ loading=lazy width="560" }
![Heating curve card](../images/cards/card-heating-curve-dark.jpg#only-dark){ loading=lazy width="560" }

### Performance

![Performance card](../images/cards/card-performance-light.jpg#only-light){ loading=lazy width="560" }
![Performance card](../images/cards/card-performance-dark.jpg#only-dark){ loading=lazy width="560" }

### System health

![System health card](../images/cards/card-system-health-light.jpg#only-light){ loading=lazy width="560" }
![System health card](../images/cards/card-system-health-dark.jpg#only-dark){ loading=lazy width="560" }

### Refrigerant circuit

![Refrigerant circuit card](../images/cards/card-refrigerant-light.jpg#only-light){ loading=lazy width="560" }
![Refrigerant circuit card](../images/cards/card-refrigerant-dark.jpg#only-dark){ loading=lazy width="560" }

### Temperatures

![Temperatures card](../images/cards/card-temperatures-light.jpg#only-light){ loading=lazy width="560" }
![Temperatures card](../images/cards/card-temperatures-dark.jpg#only-dark){ loading=lazy width="560" }

### Activity

![Activity card](../images/cards/card-activity-light.jpg#only-light){ loading=lazy width="560" }
![Activity card](../images/cards/card-activity-dark.jpg#only-dark){ loading=lazy width="560" }

### Energy per day

![Energy per day card](../images/cards/card-daily-energy-light.jpg#only-light){ loading=lazy width="560" }
![Energy per day card](../images/cards/card-daily-energy-dark.jpg#only-dark){ loading=lazy width="560" }

With a few days of history only, as here, the chart has few bars; it fills up as Home Assistant keeps statistics.

### Power today

![Power today card](../images/cards/card-power-profile-light.jpg#only-light){ loading=lazy width="560" }
![Power today card](../images/cards/card-power-profile-dark.jpg#only-dark){ loading=lazy width="560" }

### Energy signature

![Energy signature card](../images/cards/card-energy-signature-light.jpg#only-light){ loading=lazy width="560" }
![Energy signature card](../images/cards/card-energy-signature-dark.jpg#only-dark){ loading=lazy width="560" }

It needs an electricity figure (your meter, or the electricity CSNet records with a pulse meter) and at least 7 days of history for the fit.

## Less to configure

The cards take what the integration already knows:

- **Your electricity meter.** When you chose the heat pump's electricity meter in the integration settings (Reconfigure → Electricity meter of the heat pump), the cards use it for the electricity per day and the energy signature. They also find the meter's **power sensor** on the same device (for example `…_total_active_power` next to `…_total_active_energy`) and use it instead of the estimated power.
- **The electricity price** set in the Energy dashboard (grid consumption → price), to show the cost of today and of this month. With one grid source per tariff (peak and off-peak, for example), the cards use today's average: each tariff's price weighted by what it counted today. A card can set its own with `price` or `price_entity`.
- **The electricity meter's own statistics** for today and this month, when you chose a meter in the integration settings, so the overview shows what the meter counted from midnight even before the metered COP has a full day.
- **The weather forecast** of your first weather entity, for the energy signature. A card can choose another with `weather_entity`.

## A ready-made view

Paste this into a new view (dashboard → edit → ⋮ → Raw configuration editor) to get all the cards:

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
      - type: custom:csnet-power-profile-card
      - type: custom:csnet-daily-energy-card
  - type: grid
    cards:
      - type: custom:csnet-system-health-card
      - type: custom:csnet-refrigerant-card
      - type: custom:csnet-energy-signature-card
  - type: grid
    column_span: 2
    cards:
      - type: custom:csnet-temperatures-card
      - type: custom:csnet-activity-card
```

## Options

Every card accepts `title` (an empty title hides it) and `language` (`auto`, `en`, `fr` or `es`; by default the **Card language** of the integration settings, else the user's profile language). Some cards have more options, also available in the visual editor:

| Card | Option | Meaning |
|------|--------|---------|
| Heat pump | `power_entity` | A power sensor (W) to use instead of the integration's estimate, for example a real electricity meter on the heat pump's circuit |
| Heat pump | `max_power` | Value of a full gauge, in W (default 4000) |
| Heat pump, Energy signature | `price`, `price_entity` | Electricity price per kWh, instead of the Energy dashboard's |
| Temperatures, Activity | `hours` | Hours shown (default 24) |
| Energy per day | `days` | Days shown (default 14) |
| Power today | `days` | Days the average day is made of (default 14) |
| Energy signature | `days`, `weather_entity` | Days the fit is made of (default 60); weather entity for the forecast |
| Heating curve | `days` | Days of history drawn as dots (default 30, 0 for none); the last 3 days are coloured |
| System health | `pressure_min`, `pressure_max` | Normal water pressure range of your installation, in bar. Outside it, the pressure is flagged. Without them the pressure is only shown |

Any entity a card uses can be replaced with `<role>_entity`, for example `outdoor_entity: sensor.my_weather_station`. The roles:

| Role | Entity |
|------|--------|
| `power`, `heat_power`, `cop_now` | Power (your meter's power sensor when found, else the estimated consumption), output power, instant COP |
| `meter_energy`, `meter_power` | The electricity meter chosen in the integration settings, and its power sensor |
| `energy_today`, `heat_today` | Daily consumption and heat (estimated) |
| `server_heat_today` / `_yesterday` / `_month`, `server_electricity_*` | Energy recorded by CSNet |
| `cop_today`, `cop_yesterday`, `cop_month`, `cop_last_month` | COP from your electricity meter |
| `water_out`, `water_in`, `water_target`, `water_c2`, `water_flow`, `water_pressure`, `mix_valve` | Water side |
| `outdoor`, `outdoor_average` | Outdoor temperature, and the average the unit uses for its curves |
| `compressor`, `defrost`, `pump_1`, `pump_2`, `pump_3`, `backup_heater`, `boiler` | What runs |
| `compressor_frequency`, `compressor_current`, `discharge_temperature`, `evaporator_temperature`, `gas_temperature`, `liquid_temperature`, `discharge_pressure`, `suction_pressure`, `expansion_valve`, `outdoor_fan_rpm` | Refrigerant circuit |

## Heating curve card

The lines are drawn from the curve values you enter in **Settings → Devices & services → CSNet Home → Configure** (see [Heating Curve Values](Advanced-Features.md#heating-curve-values-water-law)). Without them the card still shows the unit's water target and its history, with a reminder to enter the curves.

The dots are the unit's water target, averaged per hour, against the average outdoor temperature, from Home Assistant's long-term statistics. Coloured dots are the last 3 days. Markers show the actual flow temperature and, with a mixing valve, the water of circuit 2 after the valve: the unit makes water for the warmer curve and the valve cools it for the other circuit. When the dots sit above the line, the unit is adding room compensation; below, it is in eco mode or the line does not match the unit's settings.

## Performance card

The COP needs an electricity figure. With an electricity meter chosen in the integration settings (Reconfigure → Electricity meter of the heat pump), the card shows the metered COP. Without one, it uses the electricity CSNet records when your unit has a pulse meter; otherwise it shows the heat produced only.

## Troubleshooting

- **The cards are not in the picker**: reload the browser page (the card file is loaded when the page opens). On the companion app, pull down to refresh or clear the frontend cache.
- **"CSNet Home is not set up, or this browser loaded an older version"**: the integration is not loaded, or the browser still runs a cached page from before the update. Reload the page.
- **A value shows "–"**: the unit does not report it, or the entity is disabled. Enable the entity, or replace it with `<role>_entity`.

## Energy signature card

Each past day gives a point: the electricity used against the day's average outdoor temperature. A straight line through these points (kWh = a + b × outdoor temperature) says how much more the house needs per degree colder, and, with tomorrow's forecast, about how much tomorrow will use. The fit quality (r²) tells how well the line explains the days: low values mean other things (holidays, hot water, sun) weigh more than the outdoor temperature. It needs at least 7 days of history, and is an estimate, not a promise.

The base load is the lowest hourly power of the last 14 days: what the unit draws when it does not heat (pumps, electronics).
