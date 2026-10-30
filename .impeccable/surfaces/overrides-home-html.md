---
version: 1
slug: "overrides-home-html"
primary_target: "overrides/home.html"
related_targets: ["docs/stylesheets/extra.css"]
---

# Surface: project landing (site root) + docs restyle

Mode: Persuade (landing at `/`), Read (docs pages under `/wiki/`).
Audience: HA users with a Hitachi heat pump on ATW-IOT-01 / CSNet Manager, deciding whether this works for their unit and how to install it.
Action: install from HACS (My Home Assistant link) or open the docs.
Proof: real HA screenshots in docs/images, live GitHub release/stars, verified facts (60 s polling, 3 requests, csnetmanager.com only), supported models list. No invented testimonials or counts.
Constraint: visible unofficial-API disclaimer (unaffiliated, reverse-engineered, Hitachi contacted repeatedly without reply). No Hitachi logos.

## Direction contract

THESIS: The project seen through a thermal camera: heat made visible, each zone a spot reading. Refuses the stock HACS landing (logo, tagline, feature-card grid, screenshot).

OWN-WORLD: Ironbow thermal palette (violet-black #0b0712 → #3b0f70 → #b5367a → #f2742b → #ffd24a → #fff6d6) owning whole regions; cooling register in ice blue #2e9bd6/#9ee3ff. Viewfinder HUD: thin corner brackets, crosshair spot meter, vertical temperature scale bar, tabular readouts in Martian Mono (measurements only); display Big Shoulders Display; body Hanken Grotesk. Cold/idle/unavailable states drawn as deliberately as heat (raise from seven-segment). Docs: numbered strict addressing on the scale bar (raise from teletext).

STORY: Visitor sees their own system (zones, DHW, outdoor unit) as a thermogram, learns it lands in HA as entities, trusts it because the limits are stated honestly, installs in three steps.

FIRST VIEWPORT: Full-bleed live canvas thermogram of a house cross-section (C2 radiators upstairs, C1 underfloor, DHW tank, outdoor unit). HUD top-left: name and one-line offer, Install with HACS (primary) + Read the docs. Right edge scale bar. Cursor/touch spot meter reads the field and names the zone + entity. HEAT/COOL toggle re-renders the field.

FORM: Thermogram, position 3 of my ordered list; seed 302963da.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
