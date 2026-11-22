# Sample Data

Every Hitachi unit reports a little differently: single or three phase, with or
without a suction pressure sensor, a DHW tank, two circuits, a meter. A change
that improves the figures on one unit can make them worse on another. Shared
**samples** let anyone check a change against real units before it ships.

A sample is a recording of what CSNet Manager sent to the integration, poll by
poll, with the reading of a meter when the owner has one. The samples are kept
in [csnet-home-samples](https://github.com/mmornati/csnet-home-samples), with a
[catalog](https://mmornati.github.io/csnet-home-samples/) to find them.

## Record your unit

1. Go to **Settings → Automations & scenes → Actions** (or **Developer tools →
   Actions**) and run **CSNet Home: Start sample recording**.
2. Choose how long to record. Two days or more cover the daily totals and CSNet's
   hourly heat records. A day with defrosts, a DHW cycle or cooling is worth more
   than a longer quiet period.
3. If you have a meter on the heat pump's circuit, its energy and power sensors
   are taken from the integration's settings. To record another meter, pick its
   **energy** and **power** sensors.
4. When the time is up (or when you run **CSNet Home: Stop sample recording**),
   a notification says where the file is: `csnet_home_samples/` in Home
   Assistant's configuration folder.

A restart of Home Assistant ends the recording; the file keeps what was recorded
until then.

```yaml
action: csnet_home.start_sample_recording
data:
  duration_hours: 48
  meter_power_entity: sensor.heat_pump_power
  notes: Backup heater disabled. Two cold nights.
```

## Share it

Open a [Share a sample](https://github.com/mmornati/csnet-home-samples/issues/new?template=share-sample.yml)
issue and attach the file, or open a pull request in the samples repository.

The file is redacted like the diagnostics download: the installation's name,
its position, the account, serial numbers and network identifiers are removed.
It keeps the zone names, the unit's readings and settings, the alarm history,
CSNet's energy records, and the **dates and times** of the recording, which say
when the heat pump ran. Samples are published under CC0 (public domain): look at
the file first if that matters to you.

## Test a change against the samples

From a checkout of the integration:

```bash
python scripts/fetch_samples.py --list
python scripts/fetch_samples.py --all
pytest -m replay
```

Each sample is set up as a config entry and its replies are fed to the API
client at the recorded times, with Home Assistant's clock following the sample.
The replay fails on an error logged by the integration or on an impossible
figure: a negative power, a COP out of range, a daily total going down.

To see what a change does to the figures, write a report on both branches and
compare them:

```bash
CSNET_REPLAY_REPORT=head.json pytest -m replay
git switch main
CSNET_REPLAY_REPORT=base.json pytest -m replay
python -m tests.replay.report base.json head.json
```

For each complete day this prints the estimated electricity, the heat, CSNet's
own heat and the HVAC COP, before → after, next to the meter's kWh.

The small samples in `tests/fixtures/samples/` run with every `pytest`, so the
replay itself is always tested.
