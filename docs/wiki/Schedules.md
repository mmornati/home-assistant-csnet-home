# Temperature Schedules

Change a zone's temperature at set times of the day, as the weekly programme in the CSNet app does, but from Home Assistant.

The integration has no schedule of its own: Home Assistant already does this well. This page gives two ready-made [blueprints](https://www.home-assistant.io/docs/automation/using_blueprints/), so you can set a schedule up from the UI without writing YAML.

| Blueprint | Use it when | Import |
|---|---|---|
| **Weekly schedule** | You want different time blocks per day, several per day, edited in a weekly grid | [![Import the weekly schedule blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fmmornati%2Fhome-assistant-csnet-home%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fcsnet_home%2Fcsnet_weekly_schedule.yaml) |
| **Day, bedtime and night** | The same three periods every day: a day temperature, a little warmer at bedtime, cooler at night | [![Import the day, bedtime and night blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fmmornati%2Fhome-assistant-csnet-home%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fcsnet_home%2Fcsnet_day_bedtime_night.yaml) |

Both need Home Assistant 2024.10 or later.

!!! warning "One schedule per zone"
    If the zone also has a weekly programme in the CSNet app, the two will overwrite each other's setpoint. Turn the CSNet programme off for the zones you schedule from Home Assistant.

## How both blueprints behave

- They only change the **setpoint**. They never turn the zone on or off, and never change its mode.
- They only act while the zone is in one of the modes you choose (heat only by default). For cooling, make a second automation from the same blueprint with the cooling temperatures and the **Cool** mode.
- They only send a change to CSNet when the new setpoint differs from the current one.
- They apply the right setpoint again when Home Assistant starts and when the zone is turned back on, so a restart or an off period never leaves the zone on the wrong temperature.
- If you change the setpoint by hand, it stays until the next change in the schedule, or until Home Assistant restarts or the zone is turned back on.

## Weekly schedule

This blueprint uses a Home Assistant **schedule helper** for the time blocks. While a block is running the zone gets the comfort temperature; outside the blocks it gets the eco temperature.

1. Create the schedule: **Settings → Devices & services → Helpers → Create helper → Schedule**. Name it after the zone, for example *Living room heating*, and draw the comfort blocks for each day. You can draw several blocks per day.
2. Import the blueprint with the button above, then **Create automation** from it.
3. Pick the zone, the schedule, and the comfort and eco temperatures.

To change the times later, edit the schedule helper: the automation follows it.

One schedule helper can drive several zones: create one automation per zone, each with its own temperatures.

## Day, bedtime and night

This is the simple routine: the temperature stays the same all day, goes up a little at bedtime, and drops at night.

| Input | Default | Meaning |
|---|---|---|
| Day temperature | 20 °C | Setpoint from *day starts at* until bedtime |
| Day starts at | 06:30 | |
| Bedtime starts at | 21:00 | |
| Bedtime increase | 1 °C | Added to the day temperature at bedtime. 0 to skip the bedtime period |
| Night starts at | 23:00 | Can be after midnight, for example 00:30 |
| Night decrease | 2 °C | Taken off the day temperature at night, until *day starts at* |

With the defaults: 20 °C from 06:30, 21 °C from 21:00, 18 °C from 23:00.

The same times are used every day. For different times at the weekend, or several blocks per day, use the weekly schedule instead.

## Water circuits and hot water

- **Water circuits** (C1/C2 water temperature entities) accept a setpoint only when their outdoor temperature compensation is set to a fixed temperature. Otherwise the integration ignores the change and logs a warning; see [OTC](Advanced-Features.md). Water setpoints move in whole degrees, so use whole numbers.
- **Hot water** is a water heater entity, which these blueprints do not cover. See the schedule example in [Water Heater Control](Water-Heater-Control.md#temperature-schedule).

## Writing your own

The blueprints are plain automations. To see what they do, or to start your own from them, open the automation and choose **Take control**, or read the files in the [repository](https://github.com/mmornati/home-assistant-csnet-home/tree/main/blueprints/automation/csnet_home). There is also a YAML schedule example in [Climate Control](Climate-Control.md#temperature-schedule).
