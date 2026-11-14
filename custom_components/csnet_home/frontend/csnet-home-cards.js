/*
 * Dashboard cards of the Hitachi CSNet Home integration.
 *
 * Plain web components: no build step, no third-party card. The integration
 * serves this file and Home Assistant loads it in every browser, so the cards
 * are listed in the "Add card" picker.
 *
 * The cards find their entities through the `csnet_home/dashboard` websocket
 * command (roles found by unique id), so they work with renamed entities and
 * in every language. Any role can be replaced in the card configuration with
 * `<role>_entity: sensor.something`, for example `power_entity` for a real
 * power meter.
 */

const CARD_VERSION = "1.0.0";

// ---------------------------------------------------------------------------
// Texts
// ---------------------------------------------------------------------------

const TEXTS = {
  en: {
    heat_pump: "Heat pump",
    water_circuit: "Water circuit",
    heating_curve: "Heating curve · water temperature",
    performance: "Performance · COP",
    system_health: "System health",
    refrigerant: "Refrigerant circuit",
    loading: "Loading…",
    no_integration: "CSNet Home is not set up, or this browser loaded an older version: reload the page.",
    compressor: "Compressor",
    outdoor: "Outdoor",
    water_delta: "Water ΔT",
    today: "Today",
    yesterday: "Yesterday",
    this_month: "This month",
    last_month: "Last month",
    electricity: "Electricity",
    heat: "Heat",
    cop: "COP",
    cop_now: "Right now",
    compressor_off: "compressor stopped",
    heat_only: "Without an electricity figure the COP cannot be computed: choose your heat pump's electricity meter in the integration settings (Reconfigure).",
    heat_produced: "heat produced",
    from_air: "{p} % taken from the air",
    heat_electricity: "{h} kWh of heat · {e} kWh of electricity",
    power_estimated: "Power estimated from the unit's readings",
    power_from: "Power from {name}",
    defrost: "Defrost",
    flow: "Flow",
    return: "Return",
    target: "Target",
    outdoor_unit: "Outdoor unit",
    hydro_module: "Indoor unit",
    circuit: "Circuit {n}",
    hot_water: "Hot water",
    pool: "Pool",
    mix_valve: "Mixing valve",
    setpoint: "set {v}",
    demand: "demand",
    pump: "Pump {n}",
    backup_heater: "Backup heater",
    boiler: "Boiler",
    flow_rate: "{v} m³/h",
    pressure: "{v} bar",
    water_target_now: "Water asked now",
    for_outdoor: "for {v} outside (average)",
    curve_of: "{name} curve",
    actual_flow: "Actual flow",
    history_note: "Dots: the unit's water target, hourly, over the last {d} days (darker: last 24 h).",
    curve_note: "Lines: the curves entered in the integration options. The unit can run warmer (room compensation) or cooler (eco).",
    no_curve: "Enter your heating curve values in Settings → Devices & services → CSNet Home → Configure to draw the curves.",
    unit_target: "unit target",
    all_good: "All good",
    to_check: "{n} to check",
    alarms: "Alarms",
    no_alarm: "none active",
    active_alarms: "{n} active",
    gateway: "Gateway",
    last_seen: "last contact {v}",
    central_control: "Central control",
    water_pressure: "Water pressure",
    expected_range: "expected {a} to {b} bar",
    running: "running",
    idle: "idle",
    software: "Software",
    discharge: "Discharge",
    evaporator: "Evaporator",
    gas: "Gas",
    liquid: "Liquid",
    expansion_valve: "Expansion valve",
    fan: "Outdoor fan",
    current: "Current",
    high_pressure: "High pressure",
    low_pressure: "Low pressure",
    title: "Title",
    max_power: "Gauge maximum (W)",
    days: "Days of history",
    power_entity: "Power sensor (optional)",
    pressure_min: "Lowest normal water pressure (bar, optional)",
    pressure_max: "Highest normal water pressure (bar, optional)",
  },
  fr: {
    heat_pump: "Pompe à chaleur",
    water_circuit: "Circuit d'eau",
    heating_curve: "Loi d'eau · température de départ",
    performance: "Rendement · COP",
    system_health: "Santé du système",
    refrigerant: "Circuit frigorifique",
    loading: "Chargement…",
    no_integration: "CSNet Home n'est pas configuré, ou ce navigateur a chargé une ancienne version : rechargez la page.",
    compressor: "Compresseur",
    outdoor: "Extérieur",
    water_delta: "Écart eau",
    today: "Aujourd'hui",
    yesterday: "Hier",
    this_month: "Ce mois",
    last_month: "Mois dernier",
    electricity: "Électricité",
    heat: "Chaleur",
    cop: "COP",
    cop_now: "En ce moment",
    compressor_off: "compresseur à l'arrêt",
    heat_only: "Sans mesure d'électricité, le COP ne peut pas être calculé : choisissez le compteur d'électricité de la pompe à chaleur dans les réglages de l'intégration (Reconfigurer).",
    heat_produced: "chaleur produite",
    from_air: "{p} % puisés dans l'air",
    heat_electricity: "{h} kWh de chaleur · {e} kWh d'électricité",
    power_estimated: "Puissance estimée à partir des mesures de l'unité",
    power_from: "Puissance : {name}",
    defrost: "Dégivrage",
    flow: "Départ",
    return: "Retour",
    target: "Consigne",
    outdoor_unit: "Unité extérieure",
    hydro_module: "Module hydro",
    circuit: "Circuit {n}",
    hot_water: "Eau chaude",
    pool: "Piscine",
    mix_valve: "Vanne 3 voies",
    setpoint: "consigne {v}",
    demand: "demande",
    pump: "Pompe {n}",
    backup_heater: "Appoint électrique",
    boiler: "Chaudière",
    flow_rate: "{v} m³/h",
    pressure: "{v} bar",
    water_target_now: "Eau demandée",
    for_outdoor: "pour {v} dehors (moyenne)",
    curve_of: "Loi {name}",
    actual_flow: "Départ réel",
    history_note: "Points : consigne d'eau de l'unité, par heure, sur les {d} derniers jours (plus foncés : dernières 24 h).",
    curve_note: "Lignes : les lois d'eau saisies dans les options de l'intégration. L'unité peut chauffer plus (compensation d'ambiance) ou moins (éco).",
    no_curve: "Saisissez vos lois d'eau dans Paramètres → Appareils et services → CSNet Home → Configurer pour tracer les courbes.",
    unit_target: "consigne de l'unité",
    all_good: "Tout va bien",
    to_check: "{n} à vérifier",
    alarms: "Alarmes",
    no_alarm: "aucune active",
    active_alarms: "{n} active(s)",
    gateway: "Passerelle",
    last_seen: "dernier échange {v}",
    central_control: "Contrôle central",
    water_pressure: "Pression d'eau",
    expected_range: "attendu {a} à {b} bar",
    running: "en marche",
    idle: "inactif",
    software: "Logiciel",
    discharge: "Refoulement",
    evaporator: "Évaporateur",
    gas: "Gaz",
    liquid: "Liquide",
    expansion_valve: "Détendeur",
    fan: "Ventilateur extérieur",
    current: "Courant",
    high_pressure: "Haute pression",
    low_pressure: "Basse pression",
    title: "Titre",
    max_power: "Maximum de la jauge (W)",
    days: "Jours d'historique",
    power_entity: "Capteur de puissance (facultatif)",
    pressure_min: "Pression d'eau normale minimale (bar, facultatif)",
    pressure_max: "Pression d'eau normale maximale (bar, facultatif)",
  },
  es: {
    heat_pump: "Bomba de calor",
    water_circuit: "Circuito de agua",
    heating_curve: "Curva de calefacción · temperatura del agua",
    performance: "Rendimiento · COP",
    system_health: "Estado del sistema",
    refrigerant: "Circuito frigorífico",
    loading: "Cargando…",
    no_integration: "CSNet Home no está configurado, o este navegador cargó una versión antigua: recargue la página.",
    compressor: "Compresor",
    outdoor: "Exterior",
    water_delta: "ΔT agua",
    today: "Hoy",
    yesterday: "Ayer",
    this_month: "Este mes",
    last_month: "Mes pasado",
    electricity: "Electricidad",
    heat: "Calor",
    cop: "COP",
    cop_now: "Ahora",
    compressor_off: "compresor parado",
    heat_only: "Sin una medida de electricidad no se puede calcular el COP: elija el contador de electricidad de la bomba de calor en los ajustes de la integración (Reconfigurar).",
    heat_produced: "calor producido",
    from_air: "{p} % tomado del aire",
    heat_electricity: "{h} kWh de calor · {e} kWh de electricidad",
    power_estimated: "Potencia estimada con las lecturas de la unidad",
    power_from: "Potencia: {name}",
    defrost: "Desescarche",
    flow: "Impulsión",
    return: "Retorno",
    target: "Consigna",
    outdoor_unit: "Unidad exterior",
    hydro_module: "Unidad interior",
    circuit: "Circuito {n}",
    hot_water: "Agua caliente",
    pool: "Piscina",
    mix_valve: "Válvula mezcladora",
    setpoint: "consigna {v}",
    demand: "demanda",
    pump: "Bomba {n}",
    backup_heater: "Resistencia de apoyo",
    boiler: "Caldera",
    flow_rate: "{v} m³/h",
    pressure: "{v} bar",
    water_target_now: "Agua pedida ahora",
    for_outdoor: "para {v} fuera (media)",
    curve_of: "Curva {name}",
    actual_flow: "Impulsión real",
    history_note: "Puntos: consigna de agua de la unidad, por hora, en los últimos {d} días (más oscuros: últimas 24 h).",
    curve_note: "Líneas: las curvas introducidas en las opciones de la integración. La unidad puede calentar más (compensación de ambiente) o menos (eco).",
    no_curve: "Introduzca sus curvas en Ajustes → Dispositivos y servicios → CSNet Home → Configurar para dibujarlas.",
    unit_target: "consigna de la unidad",
    all_good: "Todo bien",
    to_check: "{n} por revisar",
    alarms: "Alarmas",
    no_alarm: "ninguna activa",
    active_alarms: "{n} activa(s)",
    gateway: "Pasarela",
    last_seen: "último contacto {v}",
    central_control: "Control central",
    water_pressure: "Presión del agua",
    expected_range: "esperada de {a} a {b} bar",
    running: "en marcha",
    idle: "parado",
    software: "Software",
    discharge: "Descarga",
    evaporator: "Evaporador",
    gas: "Gas",
    liquid: "Líquido",
    expansion_valve: "Válvula de expansión",
    fan: "Ventilador exterior",
    current: "Corriente",
    high_pressure: "Alta presión",
    low_pressure: "Baja presión",
    title: "Título",
    max_power: "Máximo del indicador (W)",
    days: "Días de historial",
    power_entity: "Sensor de potencia (opcional)",
    pressure_min: "Presión de agua normal mínima (bar, opcional)",
    pressure_max: "Presión de agua normal máxima (bar, opcional)",
  },
};

function lang(hass) {
  const code = ((hass && (hass.locale?.language || hass.language)) || "en").slice(0, 2);
  return TEXTS[code] ? code : "en";
}

function t(hass, key, vars = {}) {
  const text = TEXTS[lang(hass)][key] ?? TEXTS.en[key] ?? key;
  return text.replace(/\{(\w+)\}/g, (_, name) => (vars[name] ?? ""));
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const ROLE_CACHE = new WeakMap();

/** Return the roles the integration found (cached per connection for a minute). */
function loadRoles(hass) {
  const key = hass.connection || hass;
  let cached = ROLE_CACHE.get(key);
  if (!cached || Date.now() - cached.at > 60000) {
    cached = {
      at: Date.now(),
      promise: hass.callWS({ type: "csnet_home/dashboard" }).catch((err) => ({ error: err?.message || String(err) })),
    };
    ROLE_CACHE.set(key, cached);
  }
  return cached.promise;
}

function stateOf(hass, entityId) {
  return entityId ? hass.states[entityId] : undefined;
}

function num(hass, entityId) {
  const s = stateOf(hass, entityId);
  if (!s) return null;
  const v = parseFloat(s.state);
  return Number.isFinite(v) ? v : null;
}

function isOn(hass, entityId) {
  return stateOf(hass, entityId)?.state === "on";
}

function fmt(hass, value, digits = 1) {
  if (value === null || value === undefined || !Number.isFinite(value)) return "–";
  return value.toLocaleString(hass.locale?.language || undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function friendly(hass, entityId, fallback) {
  return stateOf(hass, entityId)?.attributes?.friendly_name || fallback;
}

function shorten(text, max) {
  const value = String(text ?? "");
  return value.length > max ? `${value.slice(0, max - 1)}…` : value;
}

function relativeTime(hass, value) {
  const when = Date.parse(value);
  if (!Number.isFinite(when)) return value || "–";
  const seconds = Math.round((when - Date.now()) / 1000);
  const units = [
    ["day", 86400],
    ["hour", 3600],
    ["minute", 60],
    ["second", 1],
  ];
  const rtf = new Intl.RelativeTimeFormat(hass.locale?.language || undefined, { numeric: "auto" });
  for (const [unit, size] of units) {
    if (Math.abs(seconds) >= size || unit === "second") return rtf.format(Math.round(seconds / size), unit);
  }
  return value;
}

// ---------------------------------------------------------------------------
// Shared look
// ---------------------------------------------------------------------------

const BASE_CSS = `
  :host {
    --csnet-heat: var(--state-climate-heat-color, #ff8100);
    --csnet-cool: var(--state-climate-cool-color, #2b9af9);
    --csnet-ok: var(--success-color, #43a047);
    --csnet-warn: var(--warning-color, #ffa600);
    --csnet-bad: var(--error-color, #db4437);
    --csnet-c1: var(--csnet-heat);
    --csnet-c2: var(--success-color, #43a047);
    --csnet-muted: var(--secondary-text-color);
    --csnet-line: var(--divider-color, rgba(127,127,127,.25));
  }
  ha-card { padding: 16px; overflow: hidden; }
  .title {
    font-size: 11px; letter-spacing: .18em; text-transform: uppercase; text-align: center;
    color: var(--csnet-muted); margin: 0 0 12px;
  }
  .big { font-size: 48px; font-weight: 700; line-height: 1; font-variant-numeric: tabular-nums; letter-spacing: -.02em; }
  .unit { font-size: 14px; color: var(--csnet-muted); font-weight: 400; margin-left: 2px; }
  .muted { color: var(--csnet-muted); }
  .note { font-size: 11px; color: var(--csnet-muted); margin-top: 10px; line-height: 1.4; }
  .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px 8px; margin-top: 14px; border-top: 1px solid var(--csnet-line); padding-top: 12px; }
  .stat { text-align: center; cursor: pointer; }
  .stat .label { font-size: 10px; letter-spacing: .12em; text-transform: uppercase; color: var(--csnet-muted); }
  .stat .value { font-size: 22px; font-weight: 700; font-variant-numeric: tabular-nums; margin-top: 2px; }
  .stat .value .unit { font-size: 11px; }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
  .chip {
    font-size: 11px; letter-spacing: .06em; text-transform: uppercase; padding: 3px 9px; border-radius: 999px;
    border: 1px solid var(--csnet-line); color: var(--csnet-muted); display: inline-flex; align-items: center; gap: 5px; cursor: pointer;
  }
  .chip::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: var(--csnet-line); }
  .chip.on { color: var(--primary-text-color); border-color: color-mix(in srgb, var(--csnet-ok) 60%, transparent); background: color-mix(in srgb, var(--csnet-ok) 12%, transparent); }
  .chip.on::before { background: var(--csnet-ok); }
  .chip.heat.on { border-color: color-mix(in srgb, var(--csnet-heat) 60%, transparent); background: color-mix(in srgb, var(--csnet-heat) 12%, transparent); }
  .chip.heat.on::before { background: var(--csnet-heat); }
  .chip.cool.on { border-color: color-mix(in srgb, var(--csnet-cool) 60%, transparent); background: color-mix(in srgb, var(--csnet-cool) 12%, transparent); }
  .chip.cool.on::before { background: var(--csnet-cool); }
  [data-entity] { cursor: pointer; }
  .fan { transform-origin: center; transform-box: fill-box; }
  .spin { animation: csnet-spin 1.6s linear infinite; }
  @keyframes csnet-spin { to { transform: rotate(360deg); } }
  .flowing { stroke-dasharray: 6 8; animation: csnet-flow 1.2s linear infinite; }
  @keyframes csnet-flow { to { stroke-dashoffset: -28; } }
  @media (prefers-reduced-motion: reduce) { .spin, .flowing { animation: none; } }
  .message { padding: 8px 0; color: var(--csnet-muted); }
`;

// Fan blades centred on (0, 0), radius about 1
const FAN_PATH =
  "M0,-0.15 C0.25,-0.9 0.75,-0.75 0.55,-0.3 C0.45,-0.12 0.15,-0.05 0,0 Z " +
  "M0.13,0.075 C0.65,0.68 0.25,1.0 -0.02,0.6 C-0.12,0.42 -0.08,0.15 0,0 Z " +
  "M-0.13,0.075 C-0.9,0.22 -1.0,-0.3 -0.53,-0.3 C-0.32,-0.3 -0.12,-0.1 0,0 Z";

function fanSvg(x, y, size, spinning, color) {
  return `<g transform="translate(${x} ${y}) scale(${size})"><g class="fan ${spinning ? "spin" : ""}">
    <path d="${FAN_PATH}" fill="${color}"/><circle r="0.12" fill="${color}"/></g></g>`;
}

// ---------------------------------------------------------------------------
// Base card
// ---------------------------------------------------------------------------

class CsnetBaseCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.shadowRoot.addEventListener("click", (event) => {
      const target = event.composedPath().find((el) => el.dataset && el.dataset.entity);
      if (target) {
        this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId: target.dataset.entity }, bubbles: true, composed: true }));
      }
    });
  }

  setConfig(config) {
    this._config = { ...(config || {}) };
    this._signature = null;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._roles && !this._loading) {
      this._loading = true;
      loadRoles(hass).then((roles) => {
        this._roles = roles;
        this._loading = false;
        this._signature = null;
        this._render();
      });
    }
    this._render();
  }

  get hass() {
    return this._hass;
  }

  /** The roles, with the entities the card configuration replaces (`<role>_entity`). */
  get unit() {
    const unit = { ...(this._roles?.unit || {}) };
    for (const [key, value] of Object.entries(this._config || {})) {
      if (key.endsWith("_entity") && value) unit[key.slice(0, -"_entity".length)] = value;
    }
    return unit;
  }

  get circuits() {
    return this._roles?.circuits || [];
  }

  /** Entity ids whose state changes redraw the card. */
  watched() {
    return Object.values(this.unit);
  }

  _render() {
    if (!this._config || !this._hass) return;
    const hass = this._hass;
    if (!this._roles || this._roles.error) {
      const text = this._roles?.error ? t(hass, "no_integration") : t(hass, "loading");
      if (this._signature !== text) {
        this._signature = text;
        this.shadowRoot.innerHTML = `<style>${BASE_CSS}</style><ha-card><div class="message">${escapeHtml(text)}</div></ha-card>`;
      }
      return;
    }
    const ids = this.watched().filter(Boolean);
    const signature = JSON.stringify([lang(hass), hass.themes?.darkMode, ids.map((id) => {
      const s = hass.states[id];
      return s ? [s.state, s.last_updated] : null;
    }), this.extraSignature()]);
    if (signature === this._signature) return;
    this._signature = signature;
    this.shadowRoot.innerHTML = `<style>${BASE_CSS}${this.css()}</style><ha-card>${this.content(hass)}</ha-card>`;
  }

  extraSignature() {
    return null;
  }

  css() {
    return "";
  }

  title(hass, key) {
    const title = this._config.title ?? t(hass, key);
    return title ? `<div class="title">${escapeHtml(title)}</div>` : "";
  }

  getCardSize() {
    return 4;
  }

  /** Sections dashboards: the whole width of the section, never narrower than a third of a column. */
  getGridOptions() {
    return { columns: "full", rows: "auto", min_columns: this.constructor.minColumns };
  }

  static get minColumns() {
    return 4;
  }

  static getStubConfig() {
    return {};
  }

  static editorSchema() {
    return [{ name: "title", selector: { text: {} } }];
  }

  static getConfigElement() {
    const editor = document.createElement("csnet-home-card-editor");
    editor.schema = this.editorSchema();
    return editor;
  }
}

// ---------------------------------------------------------------------------
// Overview
// ---------------------------------------------------------------------------

class CsnetHeatPumpCard extends CsnetBaseCard {
  static editorSchema() {
    return [
      { name: "title", selector: { text: {} } },
      { name: "power_entity", selector: { entity: { domain: "sensor", device_class: "power" } } },
      { name: "max_power", selector: { number: { min: 500, max: 30000, step: 100, mode: "box" } } },
    ];
  }

  css() {
    return `
      .gauge { display: block; margin: 0 auto; width: 100%; max-width: 230px; }
      .status { text-align: center; font-size: 12px; letter-spacing: .14em; text-transform: uppercase; margin-top: 6px; }
      .status .defrost { color: var(--csnet-cool); }
      .source { font-size: 10px; color: var(--csnet-muted); text-align: center; margin-top: 10px; }
    `;
  }

  content(hass) {
    const unit = this.unit;
    const power = num(hass, unit.power);
    const maxPower = Number(this._config.max_power) || 4000;
    const running = isOn(hass, unit.compressor) || (num(hass, unit.compressor_frequency) || 0) > 0;
    const defrost = isOn(hass, unit.defrost);
    const color = defrost ? "var(--csnet-cool)" : "var(--csnet-heat)";
    const share = Math.max(0, Math.min(1, (power || 0) / maxPower));
    const r = 80;
    const length = 2 * Math.PI * r;
    const kw = power !== null && power >= 10000;
    const shown = power === null ? "–" : kw ? fmt(hass, power / 1000, 1) : fmt(hass, power, 0);
    const waterTemps = [num(hass, unit.water_out), num(hass, unit.water_in)];
    const delta = waterTemps[0] !== null && waterTemps[1] !== null ? waterTemps[0] - waterTemps[1] : null;
    const energy = num(hass, unit.energy_today) ?? num(hass, unit.server_electricity_today);
    const energyEntity = unit.energy_today || unit.server_electricity_today;
    const heat = num(hass, unit.server_heat_today) ?? num(hass, unit.heat_today);
    const heatEntity = unit.server_heat_today || unit.heat_today;
    const copEntity = num(hass, unit.cop_today) !== null ? unit.cop_today : unit.cop_today_estimated;
    const status = stateOf(hass, unit.operation_status)?.state;
    const overridden = this._config.power_entity;
    return `
      ${this.title(hass, "heat_pump")}
      <svg class="gauge" viewBox="0 0 200 200" data-entity="${escapeHtml(unit.power || "")}">
        <circle cx="100" cy="100" r="${r}" fill="none" stroke="var(--csnet-line)" stroke-width="12"/>
        <circle cx="100" cy="100" r="${r}" fill="none" stroke="${color}" stroke-width="12" stroke-linecap="round"
          stroke-dasharray="${(share * length).toFixed(1)} ${length.toFixed(1)}" transform="rotate(-90 100 100)"/>
        ${fanSvg(100, 58, 17, running, color)}
        <text x="100" y="122" text-anchor="middle" font-size="44" font-weight="700" fill="${color}">${shown}</text>
        <text x="100" y="146" text-anchor="middle" font-size="14" fill="var(--secondary-text-color)">${kw ? "kW" : "W"}</text>
      </svg>
      <div class="status">${escapeHtml(status || (running ? t(hass, "running") : t(hass, "idle")))}${defrost ? ` · <span class="defrost">${t(hass, "defrost")}</span>` : ""}</div>
      <div class="stats">
        <div class="stat" data-entity="${escapeHtml(unit.compressor_frequency || "")}"><div class="label">${t(hass, "compressor")}</div><div class="value">${fmt(hass, num(hass, unit.compressor_frequency), 0)}<span class="unit">Hz</span></div></div>
        <div class="stat" data-entity="${escapeHtml(unit.outdoor || "")}"><div class="label">${t(hass, "outdoor")}</div><div class="value" style="color:var(--csnet-cool)">${fmt(hass, num(hass, unit.outdoor))}<span class="unit">°C</span></div></div>
        <div class="stat" data-entity="${escapeHtml(unit.water_out || "")}"><div class="label">${t(hass, "water_delta")}</div><div class="value">${fmt(hass, delta)}<span class="unit">K</span></div></div>
        <div class="stat" data-entity="${escapeHtml(energyEntity || "")}"><div class="label">${t(hass, "electricity")}</div><div class="value">${fmt(hass, energy)}<span class="unit">kWh</span></div></div>
        <div class="stat" data-entity="${escapeHtml(heatEntity || "")}"><div class="label">${t(hass, "heat")}</div><div class="value" style="color:var(--csnet-heat)">${fmt(hass, heat)}<span class="unit">kWh</span></div></div>
        <div class="stat" data-entity="${escapeHtml(copEntity || "")}"><div class="label">${t(hass, "cop")}</div><div class="value" style="color:var(--csnet-ok)">${fmt(hass, num(hass, copEntity), 2)}</div></div>
      </div>
      <div class="source">${overridden ? escapeHtml(t(hass, "power_from", { name: friendly(hass, overridden, overridden) })) : t(hass, "power_estimated")} · ${t(hass, "today").toLowerCase()}</div>
    `;
  }
}

// ---------------------------------------------------------------------------
// Water circuit
// ---------------------------------------------------------------------------

class CsnetWaterCircuitCard extends CsnetBaseCard {
  static get minColumns() {
    return 6;
  }

  watched() {
    const ids = [...super.watched()];
    for (const c of this.circuits) ids.push(c.climate, c.demand, c.current_temperature);
    const dhw = this._roles?.dhw;
    if (dhw) ids.push(...Object.values(dhw));
    if (this._roles?.pool) ids.push(this._roles.pool.water_heater);
    return ids;
  }

  css() {
    return `svg.diagram { width: 100%; display: block; } .line { font-size: 12px; margin-top: 8px; }`;
  }

  content(hass) {
    const unit = this.unit;
    const running = isOn(hass, unit.compressor) || (num(hass, unit.compressor_frequency) || 0) > 0;
    const defrost = isOn(hass, unit.defrost);
    const pumping = ["pump_1", "pump_2", "pump_3"].some((p) => isOn(hass, unit[p])) || running;
    const targets = [];
    for (const c of this.circuits) {
      const climate = stateOf(hass, c.climate);
      const name = climate?.attributes?.friendly_name || t(hass, "circuit", { n: c.circuit });
      const room = climate?.attributes?.current_temperature ?? num(hass, c.current_temperature);
      targets.push({
        kind: "circuit",
        entity: c.climate,
        name,
        tag: `C${c.circuit}`,
        value: room,
        setpoint: climate?.attributes?.temperature,
        active: isOn(hass, c.demand),
        mixing: c.circuit === 2 && unit.mix_valve ? { valve: num(hass, unit.mix_valve), water: num(hass, unit.water_c2), entity: unit.mix_valve } : null,
        color: c.circuit === 1 ? "var(--csnet-c1)" : "var(--csnet-c2)",
      });
    }
    const dhw = this._roles?.dhw;
    if (dhw) {
      const heater = stateOf(hass, dhw.water_heater);
      targets.push({
        kind: "tank",
        entity: dhw.water_heater,
        name: t(hass, "hot_water"),
        tag: "DHW",
        value: heater?.attributes?.current_temperature,
        setpoint: heater?.attributes?.temperature,
        active: isOn(hass, dhw.heating),
        color: "var(--csnet-bad)",
      });
    }
    const pool = this._roles?.pool;
    if (pool) {
      const heater = stateOf(hass, pool.water_heater);
      targets.push({
        kind: "tank",
        entity: pool.water_heater,
        name: t(hass, "pool"),
        tag: "SWP",
        value: heater?.attributes?.current_temperature,
        setpoint: heater?.attributes?.temperature,
        active: false,
        color: "var(--csnet-cool)",
      });
    }

    const rowHeight = 92;
    const height = Math.max(200, targets.length * rowHeight + 20);
    const midY = height / 2;
    const hydro = { x: 200, y: midY - 60, w: 130, h: 120 };
    const outdoorBox = { x: 12, y: midY - 55, w: 140, h: 110 };
    const hot = "var(--csnet-heat)";
    const pipeClass = pumping ? "flowing" : "";

    let pipes = `<line x1="${outdoorBox.x + outdoorBox.w}" y1="${midY}" x2="${hydro.x}" y2="${midY}" stroke="${hot}" stroke-width="4" opacity=".5" class="${pipeClass}"/>`;
    let boxes = "";
    targets.forEach((target, i) => {
      const y = 10 + i * rowHeight + (height - 20 - targets.length * rowHeight) / 2;
      const box = { x: 470, y, w: 160, h: rowHeight - 14 };
      const cy = box.y + box.h / 2;
      const fromX = hydro.x + hydro.w;
      const fromY = hydro.y + 30 + (i + 0.5) * ((hydro.h - 60) / Math.max(targets.length, 1));
      const midX = 400;
      const stroke = target.active ? target.color : "var(--csnet-line)";
      pipes += `<path d="M${fromX} ${fromY} H${midX - 20} Q${midX} ${fromY} ${midX} ${fromY + (cy > fromY ? 10 : -10)} V${cy + (cy > fromY ? -10 : 10)} Q${midX} ${cy} ${midX + 20} ${cy} H${box.x}"
        fill="none" stroke="${stroke}" stroke-width="4" stroke-linecap="round" class="${target.active ? pipeClass : ""}"/>`;
      if (target.mixing) {
        pipes += `<g data-entity="${escapeHtml(target.mixing.entity)}"><circle cx="${midX}" cy="${cy}" r="17" fill="var(--card-background-color, #fff)" stroke="${target.color}" stroke-width="3"/>
          <text x="${midX}" y="${cy + 4}" text-anchor="middle" font-size="11" font-weight="700" fill="var(--primary-text-color)">${fmt(hass, target.mixing.valve, 0)}%</text>
          <text x="${midX}" y="${cy + 32}" text-anchor="middle" font-size="11" fill="${target.color}">${fmt(hass, target.mixing.water)}°</text></g>`;
      }
      boxes += `<g data-entity="${escapeHtml(target.entity)}">
        <rect x="${box.x}" y="${box.y}" width="${box.w}" height="${box.h}" rx="12" fill="color-mix(in srgb, ${target.color} 10%, transparent)" stroke="${target.color}" stroke-width="${target.active ? 2.5 : 1.2}"/>
        <text x="${box.x + box.w / 2}" y="${box.y + 20}" text-anchor="middle" font-size="10" letter-spacing="1" fill="var(--secondary-text-color)">${escapeHtml(shorten(String(target.name).toUpperCase(), 20))}</text>
        <text x="${box.x + box.w / 2}" y="${box.y + 50}" text-anchor="middle" font-size="28" font-weight="700" fill="var(--primary-text-color)">${fmt(hass, Number(target.value))}°</text>
        <text x="${box.x + box.w / 2}" y="${box.y + 68}" text-anchor="middle" font-size="10" fill="${target.color}">${target.tag} · ${escapeHtml(t(hass, "setpoint", { v: `${fmt(hass, Number(target.setpoint))}°` }))}${target.active ? ` · ${t(hass, "demand")}` : ""}</text>
      </g>`;
    });

    const outdoor = num(hass, unit.outdoor);
    const hz = num(hass, unit.compressor_frequency);
    const fanColor = defrost ? "var(--csnet-cool)" : running ? hot : "var(--secondary-text-color)";
    const diagram = `<svg class="diagram" viewBox="0 0 640 ${height}">
      ${pipes}
      <g data-entity="${escapeHtml(unit.compressor_frequency || unit.outdoor || "")}">
        <rect x="${outdoorBox.x}" y="${outdoorBox.y}" width="${outdoorBox.w}" height="${outdoorBox.h}" rx="12" fill="color-mix(in srgb, var(--csnet-cool) 8%, transparent)" stroke="var(--csnet-cool)" stroke-width="1.5"/>
        <text x="${outdoorBox.x + outdoorBox.w / 2}" y="${outdoorBox.y + 18}" text-anchor="middle" font-size="10" letter-spacing="1.5" fill="var(--secondary-text-color)">${t(hass, "outdoor_unit").toUpperCase()}</text>
        <circle cx="${outdoorBox.x + outdoorBox.w / 2}" cy="${midY + 2}" r="24" fill="none" stroke="var(--csnet-line)" stroke-width="2"/>
        ${fanSvg(outdoorBox.x + outdoorBox.w / 2, midY + 2, 19, running, fanColor)}
        <text x="${outdoorBox.x + outdoorBox.w / 2}" y="${outdoorBox.y + outdoorBox.h - 10}" text-anchor="middle" font-size="11" fill="var(--primary-text-color)">${fmt(hass, outdoor)}°C · ${fmt(hass, hz, 0)} Hz${defrost ? ` · ${t(hass, "defrost")}` : ""}</text>
      </g>
      <g data-entity="${escapeHtml(unit.water_out || "")}">
        <rect x="${hydro.x}" y="${hydro.y}" width="${hydro.w}" height="${hydro.h}" rx="12" fill="color-mix(in srgb, ${hot} 8%, transparent)" stroke="${hot}" stroke-width="1.5"/>
        <text x="${hydro.x + hydro.w / 2}" y="${hydro.y + 18}" text-anchor="middle" font-size="10" letter-spacing="1.5" fill="var(--secondary-text-color)">${t(hass, "hydro_module").toUpperCase()}</text>
        <text x="${hydro.x + hydro.w / 2}" y="${hydro.y + 40}" text-anchor="middle" font-size="11" fill="var(--secondary-text-color)">${t(hass, "flow")}</text>
        <text x="${hydro.x + hydro.w / 2}" y="${hydro.y + 64}" text-anchor="middle" font-size="24" font-weight="700" fill="${hot}">${fmt(hass, num(hass, unit.water_out))}°</text>
        <text x="${hydro.x + hydro.w / 2}" y="${hydro.y + 84}" text-anchor="middle" font-size="11" fill="var(--secondary-text-color)">${t(hass, "return")}</text>
        <text x="${hydro.x + hydro.w / 2}" y="${hydro.y + 106}" text-anchor="middle" font-size="18" font-weight="700" fill="var(--primary-text-color)">${fmt(hass, num(hass, unit.water_in))}°</text>
      </g>
      ${boxes}
    </svg>`;

    const chips = [];
    const chip = (entity, label, cls = "") => {
      if (!entity || !stateOf(hass, entity)) return;
      chips.push(`<span class="chip ${cls} ${isOn(hass, entity) ? "on" : ""}" data-entity="${escapeHtml(entity)}">${escapeHtml(label)}</span>`);
    };
    chip(unit.compressor, t(hass, "compressor"), "heat");
    chip(unit.defrost, t(hass, "defrost"), "cool");
    chip(unit.pump_1, t(hass, "pump", { n: 1 }));
    chip(unit.pump_2, t(hass, "pump", { n: 2 }));
    chip(unit.pump_3, t(hass, "pump", { n: 3 }));
    for (const c of this.circuits) chip(c.demand, `${t(hass, "demand")} C${c.circuit}`, "heat");
    if (dhw) chip(dhw.heating, t(hass, "hot_water"), "heat");
    chip(unit.backup_heater, t(hass, "backup_heater"), "heat");
    chip(unit.boiler, t(hass, "boiler"), "heat");

    const facts = [];
    if (num(hass, unit.water_flow) !== null) facts.push(`<span data-entity="${escapeHtml(unit.water_flow)}">${t(hass, "flow_rate", { v: fmt(hass, num(hass, unit.water_flow)) })}</span>`);
    if (num(hass, unit.water_pressure) !== null) facts.push(`<span data-entity="${escapeHtml(unit.water_pressure)}">${t(hass, "pressure", { v: fmt(hass, num(hass, unit.water_pressure), 2) })}</span>`);
    if (num(hass, unit.water_target) !== null) facts.push(`<span data-entity="${escapeHtml(unit.water_target)}">${t(hass, "target")} ${fmt(hass, num(hass, unit.water_target))} °C</span>`);

    return `${this.title(hass, "water_circuit")}${diagram}<div class="chips">${chips.join("")}</div>${facts.length ? `<div class="line muted">${facts.join(" · ")}</div>` : ""}`;
  }

  getCardSize() {
    return 5;
  }
}

// ---------------------------------------------------------------------------
// Heating curve
// ---------------------------------------------------------------------------

const HISTORY_CACHE = new Map();

async function loadHistory(hass, waterId, outdoorId, days) {
  const key = `${waterId}|${outdoorId}|${days}`;
  const cached = HISTORY_CACHE.get(key);
  if (cached && Date.now() - cached.at < 30 * 60000) return cached.promise;
  const end = new Date();
  const start = new Date(end.getTime() - days * 86400000);
  const promise = hass
    .callWS({
      type: "recorder/statistics_during_period",
      start_time: start.toISOString(),
      end_time: end.toISOString(),
      statistic_ids: [waterId, outdoorId],
      period: "hour",
      types: ["mean"],
    })
    .then((result) => {
      const byStart = new Map();
      const toMs = (v) => (typeof v === "number" ? v : Date.parse(v));
      for (const row of result[outdoorId] || []) if (row.mean !== null && row.mean !== undefined) byStart.set(toMs(row.start), row.mean);
      return (result[waterId] || [])
        .filter((row) => row.mean !== null && row.mean !== undefined && byStart.has(toMs(row.start)))
        .map((row) => ({ at: toMs(row.start), outdoor: byStart.get(toMs(row.start)), water: row.mean }));
    })
    .catch(() => []);
  HISTORY_CACHE.set(key, { at: Date.now(), promise });
  return promise;
}

class CsnetHeatingCurveCard extends CsnetBaseCard {
  static get minColumns() {
    return 6;
  }

  static editorSchema() {
    return [
      { name: "title", selector: { text: {} } },
      { name: "days", selector: { number: { min: 0, max: 60, step: 1, mode: "box" } } },
    ];
  }

  watched() {
    const ids = [...super.watched()];
    for (const c of this.circuits) ids.push(c.curve, c.climate);
    return ids;
  }

  extraSignature() {
    return this._history ? this._history.length : -1;
  }

  _render() {
    super._render();
    const unit = this.unit;
    const days = this._config ? Number(this._config.days ?? 7) : 7;
    if (!this._hass || !this._roles || this._roles.error || !days || !unit.water_target || !(unit.outdoor_average || unit.outdoor)) return;
    const key = `${unit.water_target}|${unit.outdoor_average || unit.outdoor}|${days}`;
    if (this._historyKey === key && (this._history || this._historyLoading)) return;
    this._historyKey = key;
    this._historyLoading = true;
    loadHistory(this._hass, unit.water_target, unit.outdoor_average || unit.outdoor, days).then((points) => {
      this._history = points;
      this._historyLoading = false;
      this._signature = null;
      super._render();
    });
  }

  css() {
    return `
      .layout { display: flex; flex-wrap: wrap; gap: 12px 18px; align-items: stretch; }
      .side { flex: 1 1 150px; min-width: 150px; }
      .chart { flex: 3 1 300px; min-width: 260px; }
      .chart svg { width: 100%; display: block; }
      .row { display: flex; justify-content: space-between; font-size: 13px; padding: 5px 0; border-bottom: 1px solid var(--csnet-line); cursor: pointer; }
      .row b { font-variant-numeric: tabular-nums; }
      .label-small { font-size: 10px; letter-spacing: .14em; text-transform: uppercase; color: var(--csnet-muted); }
    `;
  }

  content(hass) {
    const unit = this.unit;
    const outdoorId = unit.outdoor_average || unit.outdoor;
    const outdoor = num(hass, outdoorId);
    const target = num(hass, unit.water_target);
    const curves = this.circuits
      .filter((c) => c.curve && stateOf(hass, c.curve))
      .map((c) => {
        const s = stateOf(hass, c.curve);
        const climate = stateOf(hass, c.climate);
        return {
          circuit: c.circuit,
          entity: c.curve,
          name: climate?.attributes?.friendly_name || t(hass, "circuit", { n: c.circuit }),
          color: c.circuit === 1 ? "var(--csnet-c1)" : "var(--csnet-c2)",
          points: Array.isArray(s.attributes.curve) ? s.attributes.curve : [],
          value: num(hass, c.curve),
          at: s.attributes.outdoor_temperature,
        };
      });
    const history = this._history || [];
    const days = Number(this._config.days ?? 7);

    // axes
    const xs = [-20, 25, ...history.map((p) => p.outdoor), ...(outdoor !== null ? [outdoor] : [])];
    const ys = [15, 60, ...history.map((p) => p.water), ...curves.flatMap((c) => c.points.map((p) => p[1])), ...(target !== null ? [target] : [])];
    const x0 = Math.floor(Math.min(...xs) / 5) * 5;
    const x1 = Math.ceil(Math.max(...xs) / 5) * 5;
    const y0 = Math.floor(Math.min(...ys) / 10) * 10;
    const y1 = Math.ceil((Math.max(...ys) + 4) / 10) * 10;
    const W = 600;
    const H = 300;
    const pad = { l: 34, r: 12, t: 12, b: 26 };
    const sx = (v) => pad.l + ((v - x0) / (x1 - x0)) * (W - pad.l - pad.r);
    const sy = (v) => H - pad.b - ((v - y0) / (y1 - y0)) * (H - pad.t - pad.b);
    let grid = "";
    for (let x = x0; x <= x1; x += 5) {
      grid += `<line x1="${sx(x)}" x2="${sx(x)}" y1="${pad.t}" y2="${H - pad.b}" stroke="var(--csnet-line)" stroke-width="${x === 0 ? 1.4 : 0.6}"/>
        <text x="${sx(x)}" y="${H - 8}" text-anchor="middle" font-size="10" fill="var(--secondary-text-color)">${x}°</text>`;
    }
    for (let y = y0; y <= y1; y += 10) {
      grid += `<line x1="${pad.l}" x2="${W - pad.r}" y1="${sy(y)}" y2="${sy(y)}" stroke="var(--csnet-line)" stroke-width=".6"/>
        <text x="${pad.l - 6}" y="${sy(y) + 3}" text-anchor="end" font-size="10" fill="var(--secondary-text-color)">${y}°</text>`;
    }
    const recent = Date.now() - 86400000;
    const dots = history
      .map((p) => `<circle cx="${sx(p.outdoor).toFixed(1)}" cy="${sy(p.water).toFixed(1)}" r="${p.at >= recent ? 3 : 2.4}" fill="${p.at >= recent ? "var(--primary-text-color)" : "var(--secondary-text-color)"}" opacity="${p.at >= recent ? 0.55 : 0.22}"/>`)
      .join("");
    const lines = curves
      .map((c) => {
        if (!c.points.length) return "";
        const d = c.points.map((p, i) => `${i ? "L" : "M"}${sx(p[0]).toFixed(1)} ${sy(p[1]).toFixed(1)}`).join(" ");
        const anchor = c.points[Math.min(1, c.points.length - 1)];
        const now = c.value !== null && c.at !== null && c.at !== undefined
          ? `<circle cx="${sx(c.at)}" cy="${sy(c.value)}" r="6" fill="${c.color}" stroke="var(--card-background-color, #fff)" stroke-width="2"/>`
          : "";
        return `<g data-entity="${escapeHtml(c.entity)}"><path d="${d}" fill="none" stroke="${c.color}" stroke-width="3" stroke-linejoin="round"/>
          <text x="${sx(anchor[0]) + 4}" y="${Math.max(pad.t + 10, sy(anchor[1]) - 9)}" font-size="11" font-weight="600" fill="${c.color}">C${c.circuit} · ${escapeHtml(shorten(c.name, 28))}</text>${now}</g>`;
      })
      .join("");
    const unitMarker = outdoor !== null && target !== null
      ? `<g data-entity="${escapeHtml(unit.water_target)}"><circle cx="${sx(outdoor)}" cy="${sy(target)}" r="8" fill="none" stroke="var(--primary-text-color)" stroke-width="2"/>
        <text x="${sx(outdoor) + 10}" y="${sy(target) + 20}" font-size="10" fill="var(--primary-text-color)">${t(hass, "unit_target")}</text></g>`
      : "";
    const chart = `<svg viewBox="0 0 ${W} ${H}">${grid}${dots}${lines}${unitMarker}</svg>`;

    const rows = [
      [t(hass, "actual_flow"), num(hass, unit.water_out), unit.water_out],
      [t(hass, "return"), num(hass, unit.water_in), unit.water_in],
      ...curves.map((c) => [t(hass, "curve_of", { name: `C${c.circuit}` }), c.value, c.entity, c.color]),
    ]
      .filter((r) => r[2])
      .map((r) => `<div class="row" data-entity="${escapeHtml(r[2])}"><span>${escapeHtml(r[0])}</span><b style="${r[3] ? `color:${r[3]}` : ""}">${fmt(hass, r[1])}°</b></div>`)
      .join("");

    const notes = [];
    if (curves.length) notes.push(t(hass, "curve_note"));
    else notes.push(t(hass, "no_curve"));
    if (history.length) notes.push(t(hass, "history_note", { d: days }));

    return `${this.title(hass, "heating_curve")}
      <div class="layout">
        <div class="side">
          <div class="label-small">${t(hass, "water_target_now")}</div>
          <div class="big" data-entity="${escapeHtml(unit.water_target || "")}">${fmt(hass, target, 0)}<span class="unit">°C</span></div>
          <div class="muted" style="font-size:12px;margin:2px 0 10px">${escapeHtml(t(hass, "for_outdoor", { v: `${fmt(hass, outdoor)} °C` }))}</div>
          ${rows}
        </div>
        <div class="chart">${chart}</div>
      </div>
      <div class="note">${notes.map(escapeHtml).join("<br>")}</div>`;
  }

  getCardSize() {
    return 6;
  }
}

// ---------------------------------------------------------------------------
// Performance (COP)
// ---------------------------------------------------------------------------

class CsnetPerformanceCard extends CsnetBaseCard {
  css() {
    return `
      .now { display: flex; align-items: center; gap: 16px; }
      .now svg { width: 120px; flex: none; }
      .period { padding: 10px 0; border-top: 1px solid var(--csnet-line); cursor: pointer; }
      .period .head { display: flex; justify-content: space-between; align-items: baseline; }
      .period .name { font-size: 11px; letter-spacing: .14em; text-transform: uppercase; color: var(--csnet-muted); }
      .period .cop { font-size: 26px; font-weight: 700; color: var(--csnet-ok); font-variant-numeric: tabular-nums; }
      .bar { display: flex; height: 6px; border-radius: 3px; overflow: hidden; margin: 6px 0 4px; background: var(--csnet-line); }
      .bar .e { background: var(--csnet-heat); }
      .bar .a { background: var(--csnet-ok); }
      .detail { font-size: 11px; color: var(--csnet-muted); }
    `;
  }

  /** COP of a period: from the metered sensor when there is one, else from the server's heat and electricity. */
  period(hass, copRole, heatRole, electricityRole) {
    const unit = this.unit;
    const cop = stateOf(hass, unit[copRole]);
    if (cop && num(hass, unit[copRole]) !== null) {
      return { entity: unit[copRole], cop: num(hass, unit[copRole]), heat: cop.attributes.heat_kwh, electricity: cop.attributes.electricity_kwh };
    }
    const heat = num(hass, unit[heatRole]);
    const electricity = num(hass, unit[electricityRole]);
    if (heat !== null && electricity) return { entity: unit[heatRole], cop: heat / electricity, heat, electricity };
    // no electricity figure (no meter, no pulse meter): the heat alone
    if (heat !== null) return { entity: unit[heatRole], cop: null, heat, electricity: null };
    return null;
  }

  content(hass) {
    const unit = this.unit;
    const running = isOn(hass, unit.compressor) || (num(hass, unit.compressor_frequency) || 0) > 0;
    const copNow = running ? num(hass, unit.cop_now) : null;
    const share = Math.max(0, Math.min(1, (copNow || 0) / 6));
    const arc = Math.PI * 45;
    const periods = [
      ["today", this.period(hass, "cop_today", "server_heat_today", "server_electricity_today") || (num(hass, unit.cop_today_estimated) !== null ? { entity: unit.cop_today_estimated, cop: num(hass, unit.cop_today_estimated) } : null)],
      ["yesterday", this.period(hass, "cop_yesterday", "server_heat_yesterday", "server_electricity_yesterday")],
      ["this_month", this.period(hass, "cop_month", "server_heat_month", "server_electricity_month")],
      ["last_month", this.period(hass, "cop_last_month", "", "")],
    ].filter(([, p]) => p && (Number.isFinite(p.cop) || Number.isFinite(p.heat)));
    const rows = periods
      .map(([key, p]) => {
        if (!Number.isFinite(p.cop)) {
          return `<div class="period" data-entity="${escapeHtml(p.entity)}">
            <div class="head"><span class="name">${t(hass, key)}</span><span class="cop" style="color:var(--csnet-heat)">${fmt(hass, p.heat, 1)}<span class="unit">kWh</span></span></div>
            <div class="detail">${escapeHtml(t(hass, "heat_produced"))}</div></div>`;
        }
        const electricityShare = p.cop > 0 ? Math.min(1, 1 / p.cop) : 1;
        const detail = Number.isFinite(p.heat) && Number.isFinite(p.electricity)
          ? `${t(hass, "heat_electricity", { h: fmt(hass, p.heat, 1), e: fmt(hass, p.electricity, 1) })} · ${t(hass, "from_air", { p: fmt(hass, (1 - electricityShare) * 100, 0) })}`
          : t(hass, "from_air", { p: fmt(hass, (1 - electricityShare) * 100, 0) });
        return `<div class="period" data-entity="${escapeHtml(p.entity)}">
          <div class="head"><span class="name">${t(hass, key)}</span><span class="cop">${fmt(hass, p.cop, 2)}</span></div>
          <div class="bar"><div class="e" style="width:${(electricityShare * 100).toFixed(1)}%"></div><div class="a" style="width:${((1 - electricityShare) * 100).toFixed(1)}%"></div></div>
          <div class="detail">${escapeHtml(detail)}</div></div>`;
      })
      .join("");
    return `${this.title(hass, "performance")}
      <div class="now" data-entity="${escapeHtml(unit.cop_now || "")}">
        <svg viewBox="0 0 110 64">
          <path d="M10 55 A45 45 0 0 1 100 55" fill="none" stroke="var(--csnet-line)" stroke-width="9" stroke-linecap="round"/>
          <path d="M10 55 A45 45 0 0 1 100 55" fill="none" stroke="var(--csnet-ok)" stroke-width="9" stroke-linecap="round" stroke-dasharray="${(share * arc).toFixed(1)} ${arc.toFixed(1)}"/>
          <text x="55" y="54" text-anchor="middle" font-size="20" font-weight="700" fill="var(--primary-text-color)">${fmt(hass, copNow, 1)}</text>
        </svg>
        <div><div class="name muted" style="font-size:11px;letter-spacing:.14em;text-transform:uppercase">${t(hass, "cop_now")}</div>
        <div>${running ? `${fmt(hass, num(hass, unit.heat_power), 0)} W ${t(hass, "heat").toLowerCase()}` : t(hass, "compressor_off")}</div></div>
      </div>
      ${rows}
      ${periods.some(([, p]) => !Number.isFinite(p.cop)) ? `<div class="note">${escapeHtml(t(hass, "heat_only"))}</div>` : ""}`;
  }
}

// ---------------------------------------------------------------------------
// System health
// ---------------------------------------------------------------------------

class CsnetSystemHealthCard extends CsnetBaseCard {
  static editorSchema() {
    return [
      { name: "title", selector: { text: {} } },
      { name: "pressure_min", selector: { number: { min: 0, max: 10, step: 0.1, mode: "box" } } },
      { name: "pressure_max", selector: { number: { min: 0, max: 10, step: 0.1, mode: "box" } } },
    ];
  }

  watched() {
    return [...super.watched(), ...Object.values(this._roles?.gateway || {})];
  }

  css() {
    return `
      .headline { text-align: center; font-size: 22px; font-weight: 700; margin-bottom: 10px; }
      .item { display: flex; gap: 10px; align-items: center; padding: 8px 10px; border-radius: 10px; margin-top: 6px; background: color-mix(in srgb, var(--csnet-ok) 8%, transparent); cursor: pointer; }
      .item.warn { background: color-mix(in srgb, var(--csnet-warn) 14%, transparent); }
      .item.bad { background: color-mix(in srgb, var(--csnet-bad) 14%, transparent); }
      .item.info { background: color-mix(in srgb, var(--csnet-cool) 10%, transparent); }
      .dot { width: 9px; height: 9px; border-radius: 50%; background: var(--csnet-ok); flex: none; }
      .warn .dot { background: var(--csnet-warn); } .bad .dot { background: var(--csnet-bad); } .info .dot { background: var(--csnet-cool); }
      .item .name { font-size: 13px; }
      .item .detail { font-size: 11px; color: var(--csnet-muted); }
      .item .text { flex: 1; }
    `;
  }

  content(hass) {
    const unit = this.unit;
    const gateway = this._roles?.gateway || {};
    const items = [];
    const add = (level, name, detail, entity) => {
      if (entity && !stateOf(hass, entity)) return;
      items.push({ level, name, detail, entity });
    };
    const alarms = num(hass, unit.active_alarms);
    if (unit.active_alarms) add(alarms ? "bad" : "ok", t(hass, "alarms"), alarms ? t(hass, "active_alarms", { n: alarms }) : t(hass, "no_alarm"), unit.active_alarms);
    if (gateway.connectivity) {
      const conn = stateOf(hass, gateway.connectivity)?.state;
      const last = stateOf(hass, gateway.last_communication)?.state;
      const wifi = num(hass, gateway.wifi_signal);
      const bad = conn && /off|disconn|offline|lost/i.test(conn);
      const detail = [conn, last ? t(hass, "last_seen", { v: relativeTime(hass, last) }) : "", wifi !== null ? `${fmt(hass, wifi, 0)} dBm` : ""].filter(Boolean).join(" · ");
      add(bad ? "bad" : "ok", t(hass, "gateway"), detail, gateway.connectivity);
    }
    if (unit.central_control) add("ok", t(hass, "central_control"), stateOf(hass, unit.central_control)?.state, unit.central_control);
    if (unit.defrost) add(isOn(hass, unit.defrost) ? "info" : "ok", t(hass, "defrost"), isOn(hass, unit.defrost) ? t(hass, "running") : t(hass, "idle"), unit.defrost);
    for (const [role, label] of [["backup_heater", "backup_heater"], ["boiler", "boiler"]]) {
      if (unit[role] && isOn(hass, unit[role])) add("info", t(hass, label), t(hass, "running"), unit[role]);
    }
    const pressure = num(hass, unit.water_pressure);
    if (pressure !== null) {
      const min = this._config.pressure_min;
      const max = this._config.pressure_max;
      const known = min !== undefined && min !== null && max !== undefined && max !== null;
      const outside = known && (pressure < Number(min) || pressure > Number(max));
      add(outside ? "warn" : "ok", t(hass, "water_pressure"), `${fmt(hass, pressure, 2)} bar${known ? ` · ${t(hass, "expected_range", { a: fmt(hass, Number(min)), b: fmt(hass, Number(max)) })}` : ""}`, unit.water_pressure);
    }
    const toCheck = items.filter((i) => i.level === "warn" || i.level === "bad").length;
    const software = [stateOf(hass, unit.lcd_software)?.state, stateOf(hass, unit.indoor_board_software)?.state].filter((v) => v && v !== "unknown" && v !== "unavailable");
    return `${this.title(hass, "system_health")}
      <div class="headline" style="color:${toCheck ? "var(--csnet-warn)" : "var(--csnet-ok)"}">${toCheck ? t(hass, "to_check", { n: toCheck }) : t(hass, "all_good")}</div>
      ${items
        .map((i) => `<div class="item ${i.level}" data-entity="${escapeHtml(i.entity || "")}"><span class="dot"></span><div class="text"><div class="name">${escapeHtml(i.name)}</div><div class="detail">${escapeHtml(i.detail || "")}</div></div></div>`)
        .join("")}
      ${software.length ? `<div class="note">${t(hass, "software")}: ${software.map(escapeHtml).join(" · ")}</div>` : ""}`;
  }
}

// ---------------------------------------------------------------------------
// Refrigerant circuit
// ---------------------------------------------------------------------------

const REFRIGERANT_ROWS = [
  ["compressor_frequency", "compressor", "Hz", 0, 120, 0, "var(--csnet-heat)"],
  ["compressor_current", "current", "A", 0, 30, 1, "var(--csnet-heat)"],
  ["discharge_temperature", "discharge", "°C", 0, 110, 0, "var(--csnet-bad)"],
  ["evaporator_temperature", "evaporator", "°C", -30, 30, 0, "var(--csnet-cool)"],
  ["gas_temperature", "gas", "°C", -30, 110, 0, "var(--csnet-heat)"],
  ["liquid_temperature", "liquid", "°C", -30, 70, 0, "var(--csnet-cool)"],
  ["discharge_pressure", "high_pressure", "bar", 0, 45, 1, "var(--csnet-bad)"],
  ["suction_pressure", "low_pressure", "bar", 0, 20, 1, "var(--csnet-cool)"],
  ["expansion_valve", "expansion_valve", "%", 0, 100, 0, "var(--secondary-text-color)"],
  ["outdoor_fan_rpm", "fan", "rpm", 0, 1200, 0, "var(--secondary-text-color)"],
];

class CsnetRefrigerantCard extends CsnetBaseCard {
  css() {
    return `
      .r { padding: 6px 0; cursor: pointer; }
      .r .head { display: flex; justify-content: space-between; font-size: 12px; }
      .r .head b { font-variant-numeric: tabular-nums; }
      .track { height: 5px; border-radius: 3px; background: var(--csnet-line); overflow: hidden; margin-top: 4px; }
      .track div { height: 100%; border-radius: 3px; }
    `;
  }

  content(hass) {
    const unit = this.unit;
    const rows = REFRIGERANT_ROWS.filter(([role]) => unit[role] && num(hass, unit[role]) !== null)
      .map(([role, label, suffix, min, max, digits, color]) => {
        const value = num(hass, unit[role]);
        const share = Math.max(0, Math.min(1, (value - min) / (max - min)));
        const shownUnit = stateOf(hass, unit[role])?.attributes?.unit_of_measurement || suffix;
        return `<div class="r" data-entity="${escapeHtml(unit[role])}"><div class="head"><span>${t(hass, label)}</span><b>${fmt(hass, value, digits)} ${escapeHtml(shownUnit)}</b></div>
          <div class="track"><div style="width:${(share * 100).toFixed(1)}%;background:${color}"></div></div></div>`;
      })
      .join("");
    return `${this.title(hass, "refrigerant")}${rows}`;
  }
}

// ---------------------------------------------------------------------------
// Editor (shared): Home Assistant's own form element
// ---------------------------------------------------------------------------

class CsnetCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { ...(config || {}) };
    this._draw();
  }

  set hass(hass) {
    this._hass = hass;
    this._draw();
  }

  _draw() {
    if (!this._hass || !this._config) return;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.computeLabel = (field) => t(this._hass, field.name);
      this._form.addEventListener("value-changed", (event) => {
        const config = { ...event.detail.value };
        for (const key of Object.keys(config)) if (config[key] === "" || config[key] === undefined || config[key] === null) delete config[key];
        this._config = config;
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
      });
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.schema = this.schema || [];
    this._form.data = this._config;
  }
}

// ---------------------------------------------------------------------------
// Registration
// ---------------------------------------------------------------------------

const CARDS = [
  ["csnet-heat-pump-card", CsnetHeatPumpCard, "CSNet · Heat pump", "Power gauge, compressor, outdoor and water temperatures, today's energy and COP."],
  ["csnet-water-circuit-card", CsnetWaterCircuitCard, "CSNet · Water circuit", "Live diagram: outdoor unit, flow and return, each circuit and the hot water tank, pumps."],
  ["csnet-heating-curve-card", CsnetHeatingCurveCard, "CSNet · Heating curve", "The heating curves you entered, where the unit is on them now, and its water target over the last days."],
  ["csnet-performance-card", CsnetPerformanceCard, "CSNet · Performance", "COP now, today, yesterday and per month, with the share of heat taken from the air."],
  ["csnet-system-health-card", CsnetSystemHealthCard, "CSNet · System health", "Alarms, gateway, central control, defrost and water pressure at a glance."],
  ["csnet-refrigerant-card", CsnetRefrigerantCard, "CSNet · Refrigerant circuit", "Compressor, temperatures, pressures and expansion valve of the outdoor unit."],
];

if (!customElements.get("csnet-home-card-editor")) customElements.define("csnet-home-card-editor", CsnetCardEditor);
window.customCards = window.customCards || [];
for (const [tag, cls, name, description] of CARDS) {
  if (!customElements.get(tag)) customElements.define(tag, cls);
  if (!window.customCards.some((card) => card.type === tag)) {
    window.customCards.push({ type: tag, name, description, preview: true, documentationURL: "https://mmornati.github.io/home-assistant-csnet-home/" });
  }
}

console.info(`%c CSNET-HOME-CARDS %c ${CARD_VERSION} `, "color:#fff;background:#e87722;font-weight:700", "color:#e87722;background:transparent");
