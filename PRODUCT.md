# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

MkDocs Material (existing). The marketing landing is a custom MkDocs template override at the site root; the documentation pages stay in MkDocs and are restyled to match. One build, one GitHub Pages deploy (`.github/workflows/deploy-docs.yaml`).

## Users

Home Assistant users who own a Hitachi Yutaki / Yutampo heat pump (air-to-water) or a Hitachi air unit fitted with the ATW-IOT-01 module, and who manage it today through the CSNet Manager website or app. They found the project via HACS, GitHub or the HA community and want to know, quickly: does it work with my unit, what will I get in Home Assistant, how do I install it. Secondary: contributors who want to add support for their device.

## Product Purpose

A free, open-source Home Assistant custom integration (`csnet_home`) that brings Hitachi heat pumps controlled through CSNet Manager into Home Assistant: climate entities per zone (C1/C2 air and water circuits), a DHW water heater, swimming pool, dozens of sensors (temperatures, compressor, pump, pressure, power, alarms), silent mode, fan control, OTC and alarm notifications. It exists because Hitachi replaced Hi-Kumo with the ATW-IOT-01 module and offers no public API or official Home Assistant integration.

## Positioning

The only way to get an ATW-IOT-01 Hitachi system into Home Assistant without extra hardware: it talks to the same CSNet Manager cloud the official web app uses. Community built, unaffiliated with Hitachi, documented in the open.

## Operating Context

- Installed through HACS (or manually), configured through the HA UI with CSNet Manager credentials.
- Cloud polling: every 60 s by default (user configurable), 3 HTTPS requests per poll to `https://www.csnetmanager.com` only.
- Users live in HA dashboards, thermostat cards, automations and energy views.

## Capabilities and Constraints

- Unofficial: built by observing the CSNet Manager web application. Hitachi was contacted several times about an official API / HA integration and never answered. Any change on Hitachi's side can break it.
- Requires the ATW-IOT-01 module, an active CSNet Manager account and internet access.
- One CSNet account per HA instance (`single_config_entry`).
- Credentials are stored in the HA config entry and sent only to csnetmanager.com.

## Brand Commitments

- Name: "Hitachi CSNet Home" integration; domain `csnet_home`. Hitachi, Yutaki, Yutampo, CSNet are Hitachi trademarks: never imply endorsement, never use Hitachi logos.
- Existing project logo: `docs/images/logo.png`, `docs/images/logo@2x.png`.
- Author: Marco Mornati (mmornati). Apache 2.0.

## Evidence on Hand

- Real HA screenshots in `docs/images/` (thermostat card, HVAC mode selector, climate controls, integration search, config).
- Community compatibility matrix in `docs/SUPPORTED_DEVICES.md`.
- Live GitHub data (stars, latest release) via GitHub / shields.io.
- No testimonials, user counts or press exist: do not invent them.

## Product Principles

1. Honest about being unofficial: disclaimers are visible, not buried.
2. Respect the cloud it depends on: modest polling, no hammering.
3. Works for the real installs people have: multi-zone, DHW, pool, fan coils, many models.
4. Docs before issues: every feature is explained with examples and troubleshooting.
