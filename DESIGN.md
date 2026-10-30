---
name: Hitachi CSNet Home
description: The integration seen through a thermal camera; heat made visible, each zone a spot reading.
colors:
  ink-0: "#0b0712"
  ink-1: "#140c22"
  ink-2: "#1d0a3a"
  ironbow-black: "#07040f"
  ironbow-indigo: "#470f76"
  plum: "#8b2185"
  magenta: "#c5376f"
  ember: "#ea5a3a"
  orange: "#f7922a"
  amber: "#ffd24a"
  hot: "#fff6d6"
  white-hot: "#fff8e6"
  ice-hi: "#9ee3ff"
  text-2: "rgba(255, 238, 214, 0.74)"
  line: "rgba(255, 246, 214, 0.16)"
  docs-paper: "#fffcf4"
  docs-code-paper: "#f6f0e4"
  docs-link-light: "#9a2563"
  docs-night: "#120a1e"
  docs-code-night: "#1b1029"
  docs-link-dark: "#ffb35c"
  docs-header-light: "#2a1745"
typography:
  display:
    fontFamily: "Big Shoulders Display, Arial Narrow, sans-serif"
    fontSize: "clamp(2.3rem, 10vw, 5.6rem)"
    fontWeight: 900
    lineHeight: 0.97
    letterSpacing: "-0.005em"
  headline:
    fontFamily: "Big Shoulders Display, Arial Narrow, sans-serif"
    fontSize: "clamp(2.4rem, 5.6vw, 4.6rem)"
    fontWeight: 800
    lineHeight: 0.95
    letterSpacing: "0"
  title:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 700
  body:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "0.86rem"
    fontWeight: 700
    letterSpacing: "0.06em"
  readout:
    fontFamily: "Martian Mono, ui-monospace, monospace"
    fontSize: "1.6rem"
    fontWeight: 400
    lineHeight: 1.15
    fontFeature: "tnum"
  instrument:
    fontFamily: "Martian Mono, ui-monospace, monospace"
    fontSize: "0.72rem"
    fontWeight: 400
    letterSpacing: "0.08em"
rounded:
  hud: "2px"
  frame: "3px"
  mark: "9px"
spacing:
  bar-pad: "1.1rem"
  band: "clamp(5rem, 11vw, 9rem)"
  gutter: "clamp(1rem, 5.5vw, 5.5rem)"
  wrap: "76rem"
components:
  button-primary:
    backgroundColor: "{colors.amber}"
    textColor: "{colors.ink-0}"
    typography: "{typography.label}"
    rounded: "{rounded.hud}"
    padding: "0 1.35rem"
    height: "3rem"
  button-primary-hover:
    backgroundColor: "{colors.hot}"
    textColor: "{colors.ink-0}"
  button-ghost:
    backgroundColor: "rgba(11, 7, 18, 0.35)"
    textColor: "{colors.hot}"
    typography: "{typography.label}"
    rounded: "{rounded.hud}"
    padding: "0 1.35rem"
    height: "3rem"
  mode-toggle-heat-on:
    backgroundColor: "{colors.ember}"
    textColor: "{colors.ink-0}"
    typography: "{typography.instrument}"
    rounded: "{rounded.hud}"
    padding: "0.65rem 1rem"
  mode-toggle-cool-on:
    backgroundColor: "{colors.ice-hi}"
    textColor: "{colors.ink-0}"
    typography: "{typography.instrument}"
    rounded: "{rounded.hud}"
    padding: "0.65rem 1rem"
  spot-meter-card:
    backgroundColor: "rgba(11, 7, 18, 0.82)"
    textColor: "{colors.text-2}"
    typography: "{typography.instrument}"
    rounded: "{rounded.hud}"
    padding: "0.65rem 0.8rem 0.7rem"
  shot-frame:
    backgroundColor: "rgba(11, 7, 18, 0.88)"
    rounded: "{rounded.frame}"
    padding: "0.9rem"
---

# Design System: Hitachi CSNet Home

## Overview

**Creative North Star: "The Thermal Viewfinder"**

The project is shown the way an installer sees a heat pump through a thermal camera. Whole regions of the page are owned by the ironbow palette, from violet-black through magenta and ember to white-hot, and the chrome on top of them is an instrument HUD: thin corner brackets, a crosshair spot meter, a vertical temperature scale, tabular readouts. Nothing is decorated for its own sake; every device on the page reads as part of the camera or part of the report it produces.

Density is low and confident on the landing (very large condensed uppercase display, generous bands), and quiet in the docs, which keep MkDocs Material's reading layout and carry the world through the display face, a 3px ironbow strip under the header, and the custom palette. Temperature is the organising idea: sections run from cold ink to the hot amber band and back to the cold "honest" band, and cold, idle and unavailable states are drawn as deliberately as heat (ghost readings, hollow spot markers, italics for "not exposed as an entity").

The world refuses the stock HACS landing: no logo-plus-tagline hero, no feature-card grid, no screenshot as the hero. No Hitachi logos, ever (PRODUCT.md brand commitment).

**Key Characteristics:**
- Ironbow gradient as the one ordered palette; colors are positions on a temperature scale, not arbitrary accents.
- Viewfinder HUD chrome: 1.5px corner brackets, crosshair reticle, scale bar with a live mark.
- Condensed uppercase display (Big Shoulders Display) against a calm grotesque body (Hanken Grotesk).
- Martian Mono as the instrument voice: readings, addresses, identifiers, column labels.
- Near-square corners (2px) everywhere on the HUD; flat surfaces separated by hairlines.
- Cold register (ice-hi) reserved for the "how it works / honesty" band and the COOL mode.

## Colors

A single thermal scale, violet-black to white-hot, plus one ice-blue cold register; neutrals are the scale's own ends.

### Primary
- **Ironbow Amber** (amber): the hot accent. Primary button fill, focus ring, selection, the spot-meter temperature, the hot "systems" band background, step number 3.
- **Ember** (ember): HEAT mode selected state, base of the hot "dashboard" band, a mid stop of the gradient.

### Secondary
- **Thermal Magenta** (magenta): step number 1, the docs light-scheme accent and the "unofficial" admonition border/icon.
- **Plum** (plum): alternating model names on the amber band; dashboard band shadow glow.
- **Furnace Orange** (orange): step number 2; gradient stop.

### Tertiary
- **Ice Highlight** (ice-hi): the cold register. COOL mode selected state, cool-mode meter and scale mark, the data-path borders and animated flow line, fact labels, link underlines inside the honest band.

### Neutral
- **Viewfinder Black** (ink-0): page ground on the landing, docs footer and tabs, text on hot fills.
- **Night Violet** (ink-1): the manual band; docs header (Material primary).
- **Deep Indigo** (ink-2): the "how it works" cold band.
- **White-Hot Cream** (hot): primary text on dark, headings, HUD strokes.
- **Warm Ash** (text-2): secondary text and HUD labels on dark.
- **Hairline** (line): every rule and divider on dark.
- **Docs Paper / Code Paper / Night / Code Night**: docs light and dark (slate) grounds; links are wine (docs-link-light) on paper and amber-orange (docs-link-dark) at night.

### Named Rules
**The Scale Order Rule.** Every gradient that represents temperature uses the same nine stops in the same order: #07040f 0, #1d0a3a 14%, #470f76 30%, #8b2185 45%, #c5376f 58%, #ea5a3a 70%, #f7922a 81%, #ffd24a 91%, #fff8e6 100%. The canvas LUT, the scale bar, the manual index rail, the spot-dot swatches and the docs header strip all share it. Hot is always toward amber/white, cold toward violet-black; never reverse the meaning.

**The Cold Is Honest Rule.** Ice-hi marks the cold register only: COOL mode and the disclosure band (how it works, polling, traffic, credentials). It never decorates heat content.

## Typography

**Display Font:** Big Shoulders Display (with Arial Narrow, sans-serif), weights 700-900.
**Body Font:** Hanken Grotesk (with system-ui), loaded via the Material theme font.
**Label/Mono Font:** Martian Mono (with ui-monospace) on the landing; JetBrains Mono for code blocks in the docs.

**Character:** A tall, condensed, uppercase industrial display that reads like stencilled equipment labels, carried by a calm humanist grotesque; the mono is the camera talking.

### Hierarchy
- **Display** (900, clamp(2.3rem, 10vw, 5.6rem), 0.97, uppercase, balanced): the hero headline only.
- **Headline** (800, clamp(2.4rem, 5.6vw, 4.6rem), 0.95, uppercase): band titles; optionally capped at 14ch. Docs H1 is 900 at 2.6em/0.98 uppercase; docs H2 is 800 at 1.75em/1.05 uppercase.
- **Title** (Hanken 700, 1.25rem): step titles and docs H3.
- **Body** (Hanken 400, 1.0625rem, 1.55): running text, max ~33-36rem per column; lede at clamp(1.02rem, 1.3vw, 1.18rem).
- **Label** (Hanken 600-700, 0.8-0.86rem, 0.06-0.08em, uppercase): buttons, top-bar nav, footer links, text links.
- **Readout** (Martian Mono 400, 1.6rem, tabular): the live spot-meter temperature.
- **Instrument** (Martian Mono 400-500, 0.7-0.86rem, 0.05-0.08em, often uppercase): scale ends and mark, HUD meta, mode toggle, table column heads, fact and circuit terms, hostnames and entity ids, inline code.

### Named Rules
**The Instrument Voice Rule.** Martian Mono is the camera's voice: measurements, addresses (Sp1..Sp9, 01..12), hostnames, entity ids, and data labels. Prose, headings and calls to action never use it.

**The Tabular Reading Rule.** Every number that changes or is compared (meter, scale mark, docs tables) uses tabular figures.

## Layout

The landing is a stack of full-width temperature bands (vertical padding clamp(5rem, 11vw, 9rem)) inside a 76rem wrap (1rem side margins, 2rem from 48em). The hero is full-bleed, at least max(40rem, 100svh), with a live canvas filling it, copy anchored top-left at a clamp(1rem, 5.5vw, 5.5rem) gutter and the scale bar on the right edge. Content bands use a 5fr/7fr split from 60em with a sticky lead column; install uses a three-column hairline-divided row from 56em; lists of facts use auto-fit grids with no gaps, separated by rules rather than boxes.

On portrait screens (aspect ratio at or below 21/20) the hero changes composition: the scene sits above the copy, the scrim, scale bar, HUD meta and bottom disclaimer link are removed, and the meter card spans the viewport width. Below 40em, tables collapse into two-column rows and the manual index drops its description column under the title.

Docs keep MkDocs Material's three-column reading layout untouched.

## Elevation & Depth

Flat at rest. Depth comes from tonal temperature (bands change ground color) and from the thermal canvas itself, not from stacked cards. The few shadows are soft and dark-tinted, used only where an object floats over a busy image.

### Shadow Vocabulary
- **Meter lift** (`box-shadow: 0 6px 14px rgba(11, 7, 18, 0.5)`): the spot-meter card over the thermogram.
- **Shot lift** (`box-shadow: 0 14px 30px rgba(11, 7, 18, 0.3)`): screenshot frames on the hot band.
- **Reticle legibility** (`filter: drop-shadow(0 1px 2px rgba(11, 7, 18, 0.7))`): keeps the crosshair readable on any field value.

### Named Rules
**The Readable Over Heat Rule.** Any HUD text drawn over the canvas sits on a translucent ink plate (rgba(11, 7, 18, 0.72-0.82), 2px radius) rather than relying on a text shadow.

## Shapes

Near-square everywhere: 2px on buttons, toggles, HUD plates and data-path nodes; 3px on screenshot frames and inline code; circles only for spot-reading dots and the crosshair ring. The recurring silhouette is the viewfinder corner bracket: L-shaped 1.5px strokes at the four corners of the hero (1.6rem arms, cream at 55%), at two opposite corners of each screenshot frame (1rem arms, amber), and in the mark. The mark is the only rounded square (9px on a 48 grid).

## Components

### Buttons
- **Shape:** near-square (2px), 3rem minimum height, 1.35rem side padding, uppercase Hanken 700 at 0.86rem with 0.06em tracking.
- **Primary ("hot"):** amber fill, amber border, ink text; hover goes to white-hot cream.
- **Ghost:** 1.5px cream border at 50%, translucent ink fill, cream text; hover brings the border to full cream and a 10% cream wash.
- **Active:** 1px press-down. Transitions 0.25s on the expo-out ease. Focus: 2px amber outline, 3px offset.

### Mode Toggle (hvac_mode)
A segmented instrument control in mono: a lowercase `hvac_mode` label cell, then HEAT and COOL buttons. Selected HEAT fills ember, selected COOL fills ice-hi, both with ink text; unselected is ash text on transparent. The label cell hides on portrait.

### Spot Meter (signature)
A crosshair reticle (44px, 9px ring plus four ticks, 1.5px cream stroke) following pointer or touch, with a card offset to its side: zone name (Hanken 600), live temperature (readout, amber in heat, ice-hi in cool), entity id (cream), and state line (ash, hidden on narrow). Over areas with no entity it turns ghost: temperature and entity drop to ash, the entity line italic.

### Scale Bar (signature)
A 10px vertical ironbow bar with a hairline border, auto-ranged ends (heat -5..55 °C, cool 12..46 °C, interpolated during the switch) and a 0.75rem tick with a tabular value tracking the meter. Desktop/landscape only.

### Reports and Lists
- **Reading table:** mono uppercase column heads over a 40% cream rule, hairline rows, a spot column with a 0.7rem ironbow dot positioned by the reading (`--t`); ghost rows show a hollow ring.
- **Manual index:** a 4px vertical ironbow rail (hot at top), rows of mono number, display-face title and ash description; hover adds a 5% wash and nudges number and title 0.4rem right.
- **Data path:** node boxes (ice-hi 40% border, first node amber) linked by an animated dashed ice-hi flow line labelled in mono.

### Navigation
Landing top bar: transparent-to-ink gradient over the hero, brand in display 800 uppercase with the mark, links in uppercase Hanken 600 ash turning cream on hover; on mobile only Docs and the GitHub icon remain. Docs: Material header on night violet with the ironbow strip beneath, display-face site title, tabs on viewfinder black, sidebar items numbered 01-11.

### Docs Unofficial Notice
A custom `unofficial` admonition: magenta border, 10% magenta title wash, magenta warning icon.

## Do's and Don'ts

### Do:
- **Do** pick colors by temperature position on the nine-stop ironbow scale; hot content warmer, absent or idle content colder.
- **Do** draw cold, idle and unavailable states on purpose: ghost text in ash, hollow markers, italic "not exposed" lines.
- **Do** put HUD text over imagery on a translucent ink plate with a 2px radius.
- **Do** use Martian Mono with tabular figures for every measurement, address and identifier.
- **Do** keep corners at 2px (3px for image frames) and separate regions with hairlines (rgba(255, 246, 214, 0.16)).
- **Do** keep the unofficial disclaimer visible in the first viewport and in the footer.
- **Do** respect reduced motion: stop the flow line and canvas animation, render one still frame.

### Don't:
- **Don't** build a logo-tagline-feature-card-grid landing or use a screenshot as the hero.
- **Don't** use Hitachi logos or anything implying endorsement.
- **Don't** reorder or recolor the ironbow stops, or use ice-hi on heat content.
- **Don't** set prose, headings or call-to-action buttons in Martian Mono.
- **Don't** add large radii, pill shapes or stacked shadowed cards; depth comes from band temperature and the canvas.
