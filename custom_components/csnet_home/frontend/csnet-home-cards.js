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

const CARD_VERSION = "1.1.1";

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
    meter_no_history: "The meter has no history for this period yet: its COP appears once the meter has counted it.",
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
    history_note: "Dots: the unit's water target, hourly, over the last {d} days (coloured: last 3 days).",
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
    temperatures: "Water, target, outdoor and compressor",
    activity: "What ran",
    daily_energy: "Energy per day",
    power_profile: "Power today vs the usual day",
    energy_signature: "Forecast · energy signature",
    after_valve: "After the mixing valve",
    last_3_days: "last 3 days",
    before_days: "before ({d} days)",
    mixing_note: "The unit makes water for the warmer curve; the mixing valve cools it for the other circuit.",
    outdoor_mean: "Outdoor average",
    electricity_source_server: "Electricity as CSNet records it. Choose your heat pump's electricity meter in the integration settings for measured values.",
    now: "Now",
    usual_at_this_hour: "Usual at this hour ({d} days)",
    average_profile: "average day ({d} days)",
    tomorrow_weather: "Tomorrow (forecast)",
    mean_outdoor: "~{v} °C average",
    no_forecast: "no forecast available",
    no_weather: "no weather entity",
    average_7_days: "7-day average",
    per_day: "per day",
    per_degree: "Per degree colder",
    fit_quality: "per day (fit {r} %, {n} days)",
    not_enough_history: "needs at least 7 days of history",
    base_load: "Base load (14 days)",
    base_load_detail: "lowest power: pumps and electronics",
    signature_note: "Daily kWh = a + b × average outdoor temperature, over the last {d} days. An estimate, not a promise.",
    cost_today: "Cost today",
    cost_month: "Cost this month",
    price_used: "price {v} {c}/kWh",
    price: "Electricity price per kWh (optional)",
    price_entity: "Electricity price entity (optional)",
    hours: "Hours shown",
    weather_entity: "Weather entity (optional)",
    demand_of: "Demand {name}",
    needs_meter: "Needs an electricity figure: choose your heat pump's electricity meter in the integration settings (Reconfigure).",
    language: "Language (default: the integration setting)",
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
    meter_no_history: "Le compteur n'a pas encore d'historique pour cette période : son COP apparaîtra quand il l'aura mesurée.",
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
    history_note: "Points : consigne d'eau de l'unité, par heure, sur les {d} derniers jours (en couleur : 3 derniers jours).",
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
    temperatures: "Eau, consigne, extérieur et compresseur",
    activity: "Ce qui a tourné",
    daily_energy: "Énergie par jour",
    power_profile: "Puissance du jour vs journée habituelle",
    energy_signature: "Prévision · signature énergétique",
    after_valve: "Après la vanne 3 voies",
    last_3_days: "3 derniers jours",
    before_days: "avant ({d} jours)",
    mixing_note: "L'unité produit l'eau de la loi la plus chaude ; la vanne 3 voies la refroidit pour l'autre circuit.",
    outdoor_mean: "Extérieur moyen",
    electricity_source_server: "Électricité telle que CSNet l'enregistre. Choisissez le compteur d'électricité de la pompe à chaleur dans les réglages de l'intégration pour des valeurs mesurées.",
    now: "Maintenant",
    usual_at_this_hour: "Habituel à cette heure ({d} jours)",
    average_profile: "journée moyenne ({d} jours)",
    tomorrow_weather: "Demain (météo)",
    mean_outdoor: "~{v} °C en moyenne",
    no_forecast: "prévision indisponible",
    no_weather: "aucune entité météo",
    average_7_days: "Moyenne 7 jours",
    per_day: "par jour",
    per_degree: "Par degré en moins",
    fit_quality: "par jour (corrélation {r} %, {n} jours)",
    not_enough_history: "il faut au moins 7 jours d'historique",
    base_load: "Plancher (14 jours)",
    base_load_detail: "puissance la plus basse : pompes et électronique",
    signature_note: "kWh par jour = a + b × température extérieure moyenne, sur les {d} derniers jours. Une estimation, pas une promesse.",
    cost_today: "Coût du jour",
    cost_month: "Coût du mois",
    price_used: "prix {v} {c}/kWh",
    price: "Prix de l'électricité par kWh (facultatif)",
    price_entity: "Entité du prix de l'électricité (facultatif)",
    hours: "Heures affichées",
    weather_entity: "Entité météo (facultatif)",
    demand_of: "Demande {name}",
    needs_meter: "Il faut une mesure d'électricité : choisissez le compteur d'électricité de la pompe à chaleur dans les réglages de l'intégration (Reconfigurer).",
    language: "Langue (par défaut : le réglage de l'intégration)",
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
    meter_no_history: "El contador aún no tiene historial para este periodo: su COP aparecerá cuando lo haya medido.",
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
    history_note: "Puntos: consigna de agua de la unidad, por hora, en los últimos {d} días (en color: últimos 3 días).",
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
    temperatures: "Agua, consigna, exterior y compresor",
    activity: "Qué funcionó",
    daily_energy: "Energía por día",
    power_profile: "Potencia de hoy vs el día habitual",
    energy_signature: "Previsión · firma energética",
    after_valve: "Tras la válvula mezcladora",
    last_3_days: "últimos 3 días",
    before_days: "antes ({d} días)",
    mixing_note: "La unidad produce el agua de la curva más caliente; la válvula mezcladora la enfría para el otro circuito.",
    outdoor_mean: "Exterior medio",
    electricity_source_server: "Electricidad según la registra CSNet. Elija el contador de electricidad de la bomba de calor en los ajustes de la integración para valores medidos.",
    now: "Ahora",
    usual_at_this_hour: "Habitual a esta hora ({d} días)",
    average_profile: "día medio ({d} días)",
    tomorrow_weather: "Mañana (previsión)",
    mean_outdoor: "~{v} °C de media",
    no_forecast: "previsión no disponible",
    no_weather: "ninguna entidad meteorológica",
    average_7_days: "Media 7 días",
    per_day: "por día",
    per_degree: "Por grado menos",
    fit_quality: "por día (ajuste {r} %, {n} días)",
    not_enough_history: "hacen falta al menos 7 días de historial",
    base_load: "Consumo base (14 días)",
    base_load_detail: "potencia más baja: bombas y electrónica",
    signature_note: "kWh por día = a + b × temperatura exterior media, en los últimos {d} días. Una estimación, no una promesa.",
    cost_today: "Coste de hoy",
    cost_month: "Coste del mes",
    price_used: "precio {v} {c}/kWh",
    price: "Precio de la electricidad por kWh (opcional)",
    price_entity: "Entidad del precio de la electricidad (opcional)",
    hours: "Horas mostradas",
    weather_entity: "Entidad meteorológica (opcional)",
    demand_of: "Demanda {name}",
    needs_meter: "Se necesita una medida de electricidad: elija el contador de electricidad de la bomba de calor en los ajustes de la integración (Reconfigurar).",
    language: "Idioma (por defecto: el ajuste de la integración)",
  },
};

// the cards' language: the card's own, else the integration setting, else the user's profile
const CARD_LANGUAGE = Symbol("csnet card language");

function lang(hass) {
  if (hass && TEXTS[hass[CARD_LANGUAGE]]) return hass[CARD_LANGUAGE];
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

/** A number from an attribute, or null when there is none (Number(null) would be 0). */
function maybeNumber(value) {
  if (value === null || value === undefined || value === "") return null;
  const v = Number(value);
  return Number.isFinite(v) ? v : null;
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
    --csnet-flow: var(--csnet-heat);
    --csnet-return: color-mix(in srgb, var(--csnet-heat) 55%, var(--primary-text-color));
    --csnet-recent: var(--csnet-heat);
    --csnet-elec: #8e6bd8;
    --csnet-compressor: #e0b100;
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
// History and statistics
// ---------------------------------------------------------------------------

const toMs = (value) => (typeof value === "number" ? value : Date.parse(value));

/** Long-term statistics of some entities: { entity_id: [{ start (ms), mean, min, max, change, ... }] }. */
async function statistics(hass, ids, startMs, period, types, endMs = Date.now()) {
  const wanted = [...new Set(ids.filter(Boolean))];
  if (!wanted.length) return {};
  const result = await hass.callWS({
    type: "recorder/statistics_during_period",
    start_time: new Date(startMs).toISOString(),
    end_time: new Date(endMs).toISOString(),
    statistic_ids: wanted,
    period,
    types,
  });
  const out = {};
  for (const [id, rows] of Object.entries(result || {})) out[id] = rows.map((row) => ({ ...row, start: toMs(row.start) }));
  return out;
}

/** On/off history of some entities: { entity_id: [[from ms, to ms], ...] } for the "on" periods. */
async function onPeriods(hass, ids, startMs, endMs = Date.now()) {
  const wanted = [...new Set(ids.filter(Boolean))];
  if (!wanted.length) return {};
  const result = await hass.callWS({
    type: "history/history_during_period",
    start_time: new Date(startMs).toISOString(),
    end_time: new Date(endMs).toISOString(),
    entity_ids: wanted,
    minimal_response: true,
    no_attributes: true,
    significant_changes_only: false,
  });
  const out = {};
  for (const id of wanted) {
    const rows = result?.[id] || [];
    const periods = [];
    let from = null;
    for (const row of rows) {
      const at = Math.max(startMs, row.lu !== undefined ? row.lu * 1000 : toMs(row.last_updated || row.last_changed));
      const on = (row.s ?? row.state) === "on";
      if (on && from === null) from = at;
      if (!on && from !== null) {
        periods.push([from, at]);
        from = null;
      }
    }
    if (from !== null) periods.push([from, endMs]);
    out[id] = periods;
  }
  return out;
}

const PRICE_CACHE = new WeakMap();

/** The priced grid sources of the Energy dashboard: [{ entity } or { number }, with the stat they price]. */
function loadEnergyPrices(hass) {
  const key = hass.connection || hass;
  if (!PRICE_CACHE.has(key)) {
    PRICE_CACHE.set(
      key,
      hass
        .callWS({ type: "energy/get_prefs" })
        .then((prefs) => {
          const sources = [];
          for (const source of prefs?.energy_sources || []) {
            if (source.type !== "grid") continue;
            for (const flow of source.flow_from || [source]) {
              const stat = flow.stat_energy_from || null;
              if (flow.entity_energy_price) sources.push({ entity: flow.entity_energy_price, stat });
              else if (Number.isFinite(flow.number_energy_price)) sources.push({ number: flow.number_energy_price, stat });
            }
          }
          return sources;
        })
        .catch(() => []),
    );
  }
  return PRICE_CACHE.get(key);
}

/**
 * The electricity price of the Energy dashboard: { entity }, { number }, or null.
 * With one grid source per tariff (peak and off-peak, for example), { mix }:
 * each source with the kWh it counted today, so the price is today's average.
 */
async function loadEnergyPrice(hass) {
  const sources = await loadEnergyPrices(hass);
  if (!sources.length) return null;
  if (sources.length === 1) return sources[0];
  const used = await statistics(hass, sources.map((s) => s.stat), startOfDay(), "hour", ["change"]).catch(() => ({}));
  return { mix: sources.map((s) => ({ ...s, kwh: sumChange(used[s.stat]) })) };
}

/** The price per kWh a loaded price stands for, or null. */
function priceValue(hass, price) {
  if (!price) return null;
  if (price.number !== undefined) return price.number;
  if (price.entity) return num(hass, price.entity);
  if (!price.mix) return null;
  const known = price.mix.map((m) => [m.number ?? num(hass, m.entity), m.kwh || 0]).filter(([v]) => Number.isFinite(v));
  if (!known.length) return null;
  const kwh = known.reduce((sum, [, k]) => sum + k, 0);
  if (kwh > 0) return known.reduce((sum, [v, k]) => sum + v * k, 0) / kwh;
  return known.reduce((sum, [v]) => sum + v, 0) / known.length;
}

/** The entities a loaded price depends on. */
function priceEntities(price) {
  if (!price) return [];
  return price.mix ? price.mix.map((m) => m.entity).filter(Boolean) : [price.entity].filter(Boolean);
}

/** The sum of the "change" of statistics rows, or null without any. */
function sumChange(rows) {
  const values = (rows || []).map((r) => r.change).filter(Number.isFinite);
  return values.length ? values.reduce((a, b) => a + b, 0) : null;
}

/**
 * What an energy meter counted, from its long-term statistics:
 * { now: today up to now, hours: today's closed hours, yesterday, monthBefore: this month before today }.
 * The closed hours go with CSNet's heat, which is also recorded by full hours.
 */
async function meterPeriods(hass, meter) {
  if (!meter) return null;
  const today = startOfDay();
  const monthStart = new Date(today);
  monthStart.setDate(1);
  const yesterday = startOfDay(today - 1);
  const from = Math.min(monthStart.getTime(), yesterday);
  const [days, hours, recent] = await Promise.all([
    statistics(hass, [meter], from, "day", ["change"], today).catch(() => ({})),
    statistics(hass, [meter], today, "hour", ["change"]).catch(() => ({})),
    statistics(hass, [meter], today, "5minute", ["change"]).catch(() => ({})),
  ]);
  const dayRows = (days[meter] || []).filter((r) => Number.isFinite(r.change));
  // a month counts only when the meter has every day of it so far (not added in the middle of it)
  const monthRows = dayRows.filter((r) => r.start >= monthStart.getTime());
  const daysBefore = new Date(today).getDate() - 1;
  return {
    now: sumChange(recent[meter]),
    hours: sumChange(hours[meter]),
    yesterday: sumChange(dayRows.filter((r) => r.start >= yesterday)),
    monthBefore: daysBefore === 0 ? 0 : monthRows.length >= daysBefore ? sumChange(monthRows) : null,
  };
}

/** The meter's kWh of a period of the performance rows, or null. */
function meterKwh(periods, key) {
  if (!periods) return null;
  if (key === "today") return periods.hours;
  if (key === "yesterday") return periods.yesterday;
  if (key === "this_month") return periods.monthBefore !== null && periods.hours !== null ? periods.monthBefore + periods.hours : null;
  return null;
}

/** A price set on the card: a number, or an entity. Undefined when the card sets none. */
function configuredPrice(hass, config) {
  if (config.price !== undefined && config.price !== null && config.price !== "" && Number.isFinite(Number(config.price))) return Number(config.price);
  if (config.price_entity) return num(hass, config.price_entity);
  return undefined;
}

/** The daily forecast of a weather entity (first answer of the subscription), or null. */
function loadForecast(hass, entityId) {
  return new Promise((resolve) => {
    if (!entityId || !hass.connection?.subscribeMessage) {
      resolve(null);
      return;
    }
    let done = false;
    let unsubscribe = null;
    const finish = (value) => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      if (unsubscribe) unsubscribe();
      resolve(value);
    };
    const timer = setTimeout(() => finish(null), 6000);
    hass.connection
      .subscribeMessage((event) => finish(event?.forecast || null), { type: "weather/subscribe_forecast", entity_id: entityId, forecast_type: "daily" })
      .then((unsub) => {
        unsubscribe = unsub;
        if (done) unsub();
      })
      .catch(() => finish(null));
  });
}

function startOfDay(ms = Date.now()) {
  const d = new Date(ms);
  d.setHours(0, 0, 0, 0);
  return d.getTime();
}

/** Least squares y = a + b x, with r². */
function regression(points) {
  const n = points.length;
  if (n < 3) return null;
  const mx = points.reduce((s, p) => s + p[0], 0) / n;
  const my = points.reduce((s, p) => s + p[1], 0) / n;
  let sxy = 0;
  let sxx = 0;
  let syy = 0;
  for (const [x, y] of points) {
    sxy += (x - mx) * (y - my);
    sxx += (x - mx) ** 2;
    syy += (y - my) ** 2;
  }
  if (!sxx) return null;
  const b = sxy / sxx;
  return { a: my - b * mx, b, r2: syy ? (sxy * sxy) / (sxx * syy) : 0, n };
}

// ---------------------------------------------------------------------------
// Charts (plain SVG)
// ---------------------------------------------------------------------------

function niceRange(values, step, pad = 0) {
  const finite = values.filter(Number.isFinite);
  if (!finite.length) return [0, step];
  let min = Math.floor((Math.min(...finite) - pad) / step) * step;
  let max = Math.ceil((Math.max(...finite) + pad) / step) * step;
  if (min === max) max = min + step;
  return [min, max];
}

/** A round step (1, 2, 2.5 or 5 × 10^k) splitting [0, max] in about `parts` parts. */
function niceStep(max, parts = 4) {
  const raw = Math.max(max, 1e-9) / parts;
  const power = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].find((m) => m * power >= raw) * power;
  return step;
}

function hourLabel(hass, ms) {
  return new Date(ms).toLocaleTimeString(hass.locale?.language || undefined, { hour: "2-digit", minute: "2-digit" });
}

function dayLabel(hass, ms) {
  return new Date(ms).toLocaleDateString(hass.locale?.language || undefined, { day: "numeric", month: "short" });
}

/**
 * A time chart: lines (optionally filled) on a left axis and an optional right axis.
 * series: [{ points: [[ms, value]], color, width, dash, fill, axis: "right" }]
 */
function timeChart(hass, { x0, x1, series, left, right, ticks, W = 600, H = 220 }) {
  const pad = { l: 36, r: right ? 36 : 10, t: 10, b: 22 };
  const sx = (v) => pad.l + ((v - x0) / (x1 - x0 || 1)) * (W - pad.l - pad.r);
  const scale = (axis) => (v) => H - pad.b - ((v - axis.min) / (axis.max - axis.min || 1)) * (H - pad.t - pad.b);
  const syL = scale(left);
  const syR = right ? scale(right) : syL;
  let svg = "";
  for (let v = left.min; v <= left.max + 1e-9; v += left.step) {
    svg += `<line x1="${pad.l}" x2="${W - pad.r}" y1="${syL(v)}" y2="${syL(v)}" stroke="var(--csnet-line)" stroke-width=".6"/>
      <text x="${pad.l - 5}" y="${syL(v) + 3}" text-anchor="end" font-size="10" fill="var(--secondary-text-color)">${fmt(hass, v, left.digits ?? 0)}${left.suffix || ""}</text>`;
  }
  if (right) {
    for (let v = right.min; v <= right.max + 1e-9; v += right.step) {
      svg += `<text x="${W - pad.r + 5}" y="${syR(v) + 3}" font-size="10" fill="var(--secondary-text-color)">${fmt(hass, v, right.digits ?? 0)}${right.suffix || ""}</text>`;
    }
  }
  for (const [at, label] of ticks) {
    svg += `<line x1="${sx(at)}" x2="${sx(at)}" y1="${pad.t}" y2="${H - pad.b}" stroke="var(--csnet-line)" stroke-width=".5"/>
      <text x="${sx(at)}" y="${H - 6}" text-anchor="middle" font-size="10" fill="var(--secondary-text-color)">${escapeHtml(label)}</text>`;
  }
  for (const s of series) {
    const sy = s.axis === "right" ? syR : syL;
    const pts = s.points.filter((p) => Number.isFinite(p[1]) && p[0] >= x0 && p[0] <= x1);
    if (!pts.length) continue;
    const d = pts.map((p, i) => `${i ? "L" : "M"}${sx(p[0]).toFixed(1)} ${sy(p[1]).toFixed(1)}`).join(" ");
    if (s.fill) {
      const base = sy(s.axis === "right" ? right.min : left.min);
      svg += `<path d="${d} L${sx(pts[pts.length - 1][0]).toFixed(1)} ${base} L${sx(pts[0][0]).toFixed(1)} ${base} Z" fill="${s.color}" opacity="${s.fillOpacity ?? 0.18}"/>`;
    }
    svg += `<path d="${d}" fill="none" stroke="${s.color}" stroke-width="${s.width || 2}" ${s.dash ? `stroke-dasharray="${s.dash}"` : ""} stroke-linejoin="round" opacity="${s.opacity ?? 1}"/>`;
  }
  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;display:block">${svg}</svg>`;
}

function legend(items) {
  return `<div class="legend">${items
    .map(([color, label, dash]) => `<span><i style="background:${dash ? "transparent" : color};border-top:${dash ? `2px dashed ${color}` : "none"}"></i>${escapeHtml(label)}</span>`)
    .join("")}</div>`;
}

const CHART_CSS = `
  .legend { display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: 11px; color: var(--csnet-muted); margin: 4px 0 6px; }
  .legend i { display: inline-block; width: 12px; height: 3px; border-radius: 2px; margin-right: 5px; vertical-align: middle; }
  .headline-row { display: flex; flex-wrap: wrap; gap: 6px 22px; margin-bottom: 4px; }
  .headline-row .k { font-size: 10px; letter-spacing: .14em; text-transform: uppercase; color: var(--csnet-muted); }
  .headline-row .v { font-size: 22px; font-weight: 700; font-variant-numeric: tabular-nums; }
`;

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
    // a real power meter on the heat pump beats the estimate
    if (unit.meter_power) {
      unit.power_estimate = unit.power;
      unit.power = unit.meter_power;
    }
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

  /** The language this card speaks: its `language` option, else the integration's card language, else the profile's. */
  get language() {
    const own = this._config?.language;
    if (own && own !== "auto" && TEXTS[own]) return own;
    return TEXTS[this._roles?.language] ? this._roles.language : null;
  }

  /** hass, seen through the card's language. */
  _localHass(hass) {
    const code = this.language;
    return code ? Object.create(hass, { [CARD_LANGUAGE]: { value: code } }) : hass;
  }

  _render() {
    if (!this._config || !this._hass) return;
    const hass = this._localHass(this._hass);
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
    }), this.extraSignature(), this._dataAt || 0]);
    this._ensureData();
    if (signature === this._signature) return;
    this._signature = signature;
    this.shadowRoot.innerHTML = `<style>${BASE_CSS}${this.css()}</style><ha-card>${this.content(hass)}</ha-card>`;
  }

  extraSignature() {
    return null;
  }

  /** Cards that read history: what to load (null: nothing), how, and how often. */
  dataKey() {
    return null;
  }

  async fetchData() {
    return null;
  }

  refreshMs() {
    return 10 * 60000;
  }

  _ensureData() {
    const key = this.dataKey();
    if (!key || this._dataLoading) return;
    if (this._dataKey === key && Date.now() - (this._dataAt || 0) < this.refreshMs()) return;
    this._dataKey = key;
    this._dataLoading = true;
    this.fetchData(this._hass)
      .then(
        (data) => {
          this._data = data;
        },
        (err) => {
          this._data = { error: err?.message || String(err) };
        },
      )
      .finally(() => {
        this._dataLoading = false;
        this._dataAt = Date.now();
        this._render();
      });
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
    editor.schema = [...this.editorSchema(), LANGUAGE_FIELD];
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
      { name: "price", selector: { number: { min: 0, max: 5, step: 0.001, mode: "box" } } },
      { name: "price_entity", selector: { entity: {} } },
    ];
  }

  // the meter's kWh of today and of this month, and the Energy dashboard's price unless the card sets one
  dataKey() {
    const ownPrice = this._config.price || this._config.price_entity;
    const meter = this.unit.meter_energy;
    return ownPrice && !meter ? null : `${meter || ""}|${ownPrice ? "" : "energy-price"}`;
  }

  refreshMs() {
    return 10 * 60000;
  }

  async fetchData(hass) {
    const ownPrice = this._config.price || this._config.price_entity;
    const [price, meter] = await Promise.all([ownPrice ? null : loadEnergyPrice(hass), meterPeriods(hass, this.unit.meter_energy)]);
    return {
      price,
      meter,
      meterToday: meter?.now ?? null,
      meterMonth: meter && meter.now !== null && meter.monthBefore !== null ? meter.monthBefore + meter.now : null,
    };
  }

  price(hass) {
    const own = configuredPrice(hass, this._config);
    return own !== undefined ? own : priceValue(hass, this._data?.price);
  }

  watched() {
    return [...super.watched(), this._config.price_entity, ...priceEntities(this._data?.price)];
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
    // electricity: the user's meter, else the estimate, else CSNet's record
    const metered = (role) => {
      const raw = stateOf(hass, unit[role])?.attributes?.electricity_kwh;
      const v = raw === null || raw === undefined || raw === "" ? NaN : Number(raw);
      return Number.isFinite(v) ? v : null;
    };
    const meterToday = Number.isFinite(this._data?.meterToday) ? this._data.meterToday : null;
    const meterMonth = Number.isFinite(this._data?.meterMonth) ? this._data.meterMonth : null;
    const energy = meterToday ?? metered("cop_today") ?? num(hass, unit.energy_today) ?? num(hass, unit.server_electricity_today);
    const energyEntity = meterToday !== null ? unit.meter_energy : metered("cop_today") !== null ? unit.cop_today : unit.energy_today || unit.server_electricity_today;
    const month = meterMonth ?? metered("cop_month") ?? num(hass, unit.server_electricity_month);
    const monthEntity = meterMonth !== null ? unit.meter_energy : metered("cop_month") !== null ? unit.cop_month : unit.server_electricity_month;
    const price = this.price(hass);
    const currency = escapeHtml(hass.config?.currency || "€");
    const heat = num(hass, unit.server_heat_today) ?? num(hass, unit.heat_today);
    const heatEntity = unit.server_heat_today || unit.heat_today;
    // COP: the metered sensor, else heat over the meter's closed hours, else the estimate
    const meterHours = meterKwh(this._data?.meter, "today");
    const heatHours = num(hass, unit.server_heat_today);
    const copFromMeter = num(hass, unit.cop_today) === null && heatHours !== null && meterHours > 0 ? heatHours / meterHours : null;
    const copEntity = num(hass, unit.cop_today) !== null ? unit.cop_today : copFromMeter !== null ? unit.meter_energy : unit.cop_today_estimated;
    const copValue = copFromMeter ?? num(hass, copEntity);
    const status = stateOf(hass, unit.operation_status)?.state;
    const overridden = this._config.power_entity || (unit.meter_power && unit.power === unit.meter_power ? unit.meter_power : null);
    const extra = [];
    if (price !== null && energy !== null) extra.push([energyEntity, t(hass, "cost_today"), `${fmt(hass, energy * price, 2)}<span class="unit">${currency}</span>`, "var(--csnet-heat)"]);
    if (month > 0) extra.push([monthEntity, t(hass, "this_month"), `${fmt(hass, month, 0)}<span class="unit">kWh</span>`, ""]);
    if (price !== null && month > 0) extra.push([monthEntity, t(hass, "cost_month"), `${fmt(hass, month * price, 2)}<span class="unit">${currency}</span>`, "var(--csnet-heat)"]);
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
        <div class="stat" data-entity="${escapeHtml(copEntity || "")}"><div class="label">${t(hass, "cop")}</div><div class="value" style="color:var(--csnet-ok)">${fmt(hass, copValue, 2)}</div></div>
        ${extra.map(([id, label, value, color]) => `<div class="stat" data-entity="${escapeHtml(id || "")}"><div class="label">${escapeHtml(label)}</div><div class="value" style="${color ? `color:${color}` : ""}">${value}</div></div>`).join("")}
      </div>
      <div class="source">${overridden ? escapeHtml(t(hass, "power_from", { name: friendly(hass, overridden, overridden) })) : t(hass, "power_estimated")}${price !== null ? ` · ${escapeHtml(t(hass, "price_used", { v: fmt(hass, price, 3), c: hass.config?.currency || "€" }))}` : ""}</div>
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
        <text x="${box.x + box.w / 2}" y="${box.y + 50}" text-anchor="middle" font-size="28" font-weight="700" fill="var(--primary-text-color)">${fmt(hass, maybeNumber(target.value))}°</text>
        <text x="${box.x + box.w / 2}" y="${box.y + 68}" text-anchor="middle" font-size="10" fill="${target.color}">${target.tag} · ${escapeHtml(t(hass, "setpoint", { v: `${fmt(hass, maybeNumber(target.setpoint))}°` }))}${target.active ? ` · ${t(hass, "demand")}` : ""}</text>
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

class CsnetHeatingCurveCard extends CsnetBaseCard {
  static get minColumns() {
    return 6;
  }

  static editorSchema() {
    return [
      { name: "title", selector: { text: {} } },
      { name: "days", selector: { number: { min: 0, max: 365, step: 1, mode: "box" } } },
    ];
  }

  watched() {
    const ids = [...super.watched()];
    for (const c of this.circuits) ids.push(c.curve, c.climate);
    return ids;
  }

  get days() {
    return Number(this._config.days ?? 30);
  }

  dataKey() {
    const unit = this.unit;
    const outdoor = unit.outdoor_average || unit.outdoor;
    return this.days > 0 && unit.water_target && outdoor ? `${unit.water_target}|${outdoor}|${this.days}` : null;
  }

  refreshMs() {
    return 30 * 60000;
  }

  /** The unit's water target against the average outdoor temperature, hourly. */
  async fetchData(hass) {
    const unit = this.unit;
    const outdoorId = unit.outdoor_average || unit.outdoor;
    const stats = await statistics(hass, [unit.water_target, outdoorId], Date.now() - this.days * 86400000, "hour", ["mean"]);
    const outdoorByHour = new Map((stats[outdoorId] || []).filter((r) => Number.isFinite(r.mean)).map((r) => [r.start, r.mean]));
    return (stats[unit.water_target] || [])
      .filter((r) => Number.isFinite(r.mean) && outdoorByHour.has(r.start))
      .map((r) => ({ at: r.start, outdoor: outdoorByHour.get(r.start), water: r.mean }));
  }

  css() {
    return `${CHART_CSS}
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
    const flow = num(hass, unit.water_out);
    const afterValve = unit.mix_valve ? num(hass, unit.water_c2) : null;
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
    const history = Array.isArray(this._data) ? this._data : [];
    const days = this.days;

    // axes
    const xs = [-20, 25, ...history.map((p) => p.outdoor), ...(outdoor !== null ? [outdoor] : [])];
    const ys = [15, 60, ...history.map((p) => p.water), ...curves.flatMap((c) => c.points.map((p) => p[1])), target, flow, afterValve].filter(Number.isFinite);
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
    // last 3 days darker and warmer than the older points
    const recent = Date.now() - 3 * 86400000;
    const older = history.filter((p) => p.at < recent);
    const latest = history.filter((p) => p.at >= recent);
    const dots =
      older.map((p) => `<circle cx="${sx(p.outdoor).toFixed(1)}" cy="${sy(p.water).toFixed(1)}" r="2.3" fill="var(--secondary-text-color)" opacity=".22"/>`).join("") +
      latest.map((p) => `<circle cx="${sx(p.outdoor).toFixed(1)}" cy="${sy(p.water).toFixed(1)}" r="3" fill="var(--csnet-recent)" opacity=".6"/>`).join("");
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
    let markers = "";
    if (outdoor !== null && flow !== null) {
      markers += `<g data-entity="${escapeHtml(unit.water_out)}"><rect x="${sx(outdoor) - 4}" y="${sy(flow) - 4}" width="8" height="8" fill="var(--csnet-flow)" transform="rotate(45 ${sx(outdoor)} ${sy(flow)})"/></g>`;
    }
    if (outdoor !== null && afterValve !== null) {
      markers += `<g data-entity="${escapeHtml(unit.water_c2)}"><circle cx="${sx(outdoor)}" cy="${sy(afterValve)}" r="5" fill="var(--csnet-c2)" stroke="var(--card-background-color, #fff)" stroke-width="1.5"/></g>`;
    }
    if (outdoor !== null && target !== null) {
      markers += `<g data-entity="${escapeHtml(unit.water_target)}"><circle cx="${sx(outdoor)}" cy="${sy(target)}" r="8" fill="none" stroke="var(--primary-text-color)" stroke-width="2"/>
        <text x="${sx(outdoor) + 10}" y="${sy(target) + 20}" font-size="10" fill="var(--primary-text-color)">${t(hass, "unit_target")}</text></g>`;
    }
    const chart = `<svg viewBox="0 0 ${W} ${H}">${grid}${dots}${lines}${markers}</svg>`;

    const legendItems = [["var(--primary-text-color)", t(hass, "unit_target")]];
    if (flow !== null) legendItems.push(["var(--csnet-flow)", t(hass, "actual_flow")]);
    if (afterValve !== null) legendItems.push(["var(--csnet-c2)", t(hass, "after_valve")]);
    if (latest.length) legendItems.push(["var(--csnet-recent)", t(hass, "last_3_days")]);
    if (older.length) legendItems.push(["var(--secondary-text-color)", t(hass, "before_days", { d: days })]);

    const rows = [
      [t(hass, "actual_flow"), flow, unit.water_out],
      [t(hass, "return"), num(hass, unit.water_in), unit.water_in],
      ...(afterValve !== null ? [[t(hass, "after_valve"), afterValve, unit.water_c2, "var(--csnet-c2)"]] : []),
      ...curves.map((c) => [t(hass, "curve_of", { name: `C${c.circuit}` }), c.value, c.entity, c.color]),
    ]
      .filter((r) => r[2])
      .map((r) => `<div class="row" data-entity="${escapeHtml(r[2])}"><span>${escapeHtml(r[0])}</span><b style="${r[3] ? `color:${r[3]}` : ""}">${fmt(hass, r[1])}°</b></div>`)
      .join("");

    const notes = [];
    if (curves.length) notes.push(t(hass, "curve_note"));
    else notes.push(t(hass, "no_curve"));
    if (curves.length > 1 && unit.mix_valve) notes.push(t(hass, "mixing_note"));
    if (history.length) notes.push(t(hass, "history_note", { d: days }));

    return `${this.title(hass, "heating_curve")}
      <div class="layout">
        <div class="side">
          <div class="label-small">${t(hass, "water_target_now")}</div>
          <div class="big" data-entity="${escapeHtml(unit.water_target || "")}">${fmt(hass, target, 0)}<span class="unit">°C</span></div>
          <div class="muted" style="font-size:12px;margin:2px 0 10px">${escapeHtml(t(hass, "for_outdoor", { v: `${fmt(hass, outdoor)} °C` }))}</div>
          ${rows}
        </div>
        <div class="chart">${chart}${legend(legendItems)}</div>
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

  // the meter's history, for the periods its COP sensors have not measured from their start
  dataKey() {
    return this.unit.meter_energy || null;
  }

  async fetchData(hass) {
    return meterPeriods(hass, this.unit.meter_energy);
  }

  /** COP of a period: the metered sensor, else heat over the meter's history, else the server's heat and electricity. */
  period(hass, copRole, heatRole, electricityRole, key) {
    const unit = this.unit;
    const cop = stateOf(hass, unit[copRole]);
    if (cop && num(hass, unit[copRole]) !== null) {
      return { entity: unit[copRole], cop: num(hass, unit[copRole]), heat: cop.attributes.heat_kwh, electricity: cop.attributes.electricity_kwh };
    }
    const heat = num(hass, unit[heatRole]);
    const metered = meterKwh(this._data, key);
    if (heat !== null && metered > 0) return { entity: unit.meter_energy, cop: heat / metered, heat, electricity: metered };
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
      ["today", this.period(hass, "cop_today", "server_heat_today", "server_electricity_today", "today") || (num(hass, unit.cop_today_estimated) !== null ? { entity: unit.cop_today_estimated, cop: num(hass, unit.cop_today_estimated) } : null)],
      ["yesterday", this.period(hass, "cop_yesterday", "server_heat_yesterday", "server_electricity_yesterday", "yesterday")],
      ["this_month", this.period(hass, "cop_month", "server_heat_month", "server_electricity_month", "this_month")],
      ["last_month", this.period(hass, "cop_last_month", "", "", "last_month")],
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
      ${periods.some(([, p]) => !Number.isFinite(p.cop)) ? `<div class="note">${escapeHtml(t(hass, unit.meter_energy ? "meter_no_history" : "heat_only"))}</div>` : ""}`;
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
// Temperatures over the last hours
// ---------------------------------------------------------------------------

class CsnetTemperaturesCard extends CsnetBaseCard {
  static get minColumns() {
    return 6;
  }

  static editorSchema() {
    return [
      { name: "title", selector: { text: {} } },
      { name: "hours", selector: { number: { min: 3, max: 240, step: 1, mode: "box" } } },
    ];
  }

  get hours() {
    return Number(this._config.hours ?? 24);
  }

  lines() {
    const unit = this.unit;
    return [
      ["water_out", "flow", "var(--csnet-flow)", 2.4],
      ["water_in", "return", "var(--csnet-return)", 1.6],
      ["water_c2", "after_valve", "var(--csnet-c2)", 1.6],
      ["water_target", "target", "var(--primary-text-color)", 1.4, "5 4"],
      ["outdoor", "outdoor", "var(--csnet-cool)", 1.8],
    ].filter(([role]) => unit[role] && (role !== "water_c2" || unit.mix_valve));
  }

  dataKey() {
    const unit = this.unit;
    const ids = [...this.lines().map(([role]) => unit[role]), unit.compressor_frequency].filter(Boolean);
    return ids.length ? `${ids.join("|")}|${this.hours}` : null;
  }

  refreshMs() {
    return 5 * 60000;
  }

  async fetchData(hass) {
    const unit = this.unit;
    const start = Date.now() - this.hours * 3600000;
    const ids = [...this.lines().map(([role]) => unit[role]), unit.compressor_frequency];
    return { start, stats: await statistics(hass, ids, start, this.hours > 48 ? "hour" : "5minute", ["mean"]) };
  }

  css() {
    return CHART_CSS;
  }

  content(hass) {
    const unit = this.unit;
    const data = this._data && !this._data.error ? this._data : { start: Date.now() - this.hours * 3600000, stats: {} };
    const x1 = Date.now();
    const x0 = data.start;
    const points = (id) => (data.stats[id] || []).map((r) => [r.start, r.mean]);
    const series = this.lines().map(([role, , color, width, dash]) => ({ points: points(unit[role]), color, width, dash }));
    const temps = series.flatMap((s) => s.points.map((p) => p[1]));
    const [lmin, lmax] = niceRange(temps.length ? temps : [0, 50], 10);
    const hz = points(unit.compressor_frequency);
    const right = hz.length ? { min: 0, max: Math.max(60, niceRange(hz.map((p) => p[1]), 20)[1]), step: 20, suffix: "" } : null;
    if (hz.length) series.unshift({ points: hz, color: "var(--csnet-compressor)", width: 1, fill: true, fillOpacity: 0.25, axis: "right", opacity: 0.6 });
    const ticks = [];
    const tickStep = this.hours > 48 ? 24 * 3600000 : this.hours > 12 ? 6 * 3600000 : 3600000 * 2;
    for (let at = Math.ceil(x0 / tickStep) * tickStep; at <= x1; at += tickStep) ticks.push([at, this.hours > 48 ? dayLabel(hass, at) : hourLabel(hass, at)]);
    const chart = timeChart(hass, { x0, x1, series, left: { min: lmin, max: lmax, step: 10, suffix: "°" }, right, ticks });
    const items = this.lines().map(([role, label, color, , dash]) => [color, `${t(hass, label)}: ${fmt(hass, num(hass, unit[role]))} °C`, dash]);
    if (hz.length) items.push(["var(--csnet-compressor)", `${t(hass, "compressor")}: ${fmt(hass, num(hass, unit.compressor_frequency), 0)} Hz`]);
    return `${this.title(hass, "temperatures")}${legend(items)}${chart}`;
  }
}

// ---------------------------------------------------------------------------
// What ran over the last hours
// ---------------------------------------------------------------------------

class CsnetActivityCard extends CsnetBaseCard {
  static get minColumns() {
    return 6;
  }

  static editorSchema() {
    return [
      { name: "title", selector: { text: {} } },
      { name: "hours", selector: { number: { min: 1, max: 168, step: 1, mode: "box" } } },
    ];
  }

  get hours() {
    return Number(this._config.hours ?? 24);
  }

  rows() {
    const hass = this._hass;
    const unit = this.unit;
    const rows = [
      [unit.compressor, t(hass, "compressor"), "var(--csnet-heat)"],
      [unit.defrost, t(hass, "defrost"), "var(--csnet-cool)"],
      ...this.circuits.map((c) => [c.demand, t(hass, "demand_of", { name: friendly(hass, c.climate, `C${c.circuit}`) }), c.circuit === 1 ? "var(--csnet-c1)" : "var(--csnet-c2)"]),
      [this._roles?.dhw?.heating, t(hass, "hot_water"), "var(--csnet-bad)"],
      [unit.pump_1, t(hass, "pump", { n: 1 }), "var(--csnet-ok)"],
      [unit.pump_2, t(hass, "pump", { n: 2 }), "var(--csnet-ok)"],
      [unit.pump_3, t(hass, "pump", { n: 3 }), "var(--csnet-ok)"],
      [unit.backup_heater, t(hass, "backup_heater"), "var(--csnet-bad)"],
      [unit.boiler, t(hass, "boiler"), "var(--csnet-bad)"],
    ];
    return rows.filter(([id]) => id && stateOf(hass, id));
  }

  dataKey() {
    const ids = this.rows().map(([id]) => id);
    return ids.length ? `${ids.join("|")}|${this.hours}` : null;
  }

  refreshMs() {
    return 5 * 60000;
  }

  async fetchData(hass) {
    const start = Date.now() - this.hours * 3600000;
    return { start, periods: await onPeriods(hass, this.rows().map(([id]) => id), start) };
  }

  css() {
    return `
      .tl { display: grid; grid-template-columns: minmax(90px, 28%) 1fr auto; gap: 6px 10px; align-items: center; font-size: 12px; }
      .tl .name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; }
      .tl .bar { position: relative; height: 14px; border-radius: 4px; background: var(--csnet-line); overflow: hidden; cursor: pointer; }
      .tl .bar span { position: absolute; top: 0; bottom: 0; border-radius: 2px; }
      .tl .total { font-variant-numeric: tabular-nums; color: var(--csnet-muted); text-align: right; }
      .axis { display: flex; justify-content: space-between; font-size: 10px; color: var(--csnet-muted); margin: 4px 0 0 calc(28% + 10px); padding-right: 60px; }
    `;
  }

  content(hass) {
    const data = this._data && !this._data.error ? this._data : null;
    const x1 = Date.now();
    const x0 = data ? data.start : x1 - this.hours * 3600000;
    const span = x1 - x0;
    const duration = (ms) => {
      const minutes = Math.round(ms / 60000);
      return minutes >= 60 ? `${Math.floor(minutes / 60)} h ${String(minutes % 60).padStart(2, "0")}` : `${minutes} min`;
    };
    const rows = this.rows()
      .map(([id, label, color]) => {
        const periods = data?.periods?.[id] || [];
        const total = periods.reduce((sum, [a, b]) => sum + (b - a), 0);
        const spans = periods
          .map(([a, b]) => `<span style="left:${(((a - x0) / span) * 100).toFixed(2)}%;width:${Math.max(0.3, ((b - a) / span) * 100).toFixed(2)}%;background:${color}"></span>`)
          .join("");
        return `<div class="name" data-entity="${escapeHtml(id)}" title="${escapeHtml(label)}">${escapeHtml(label)}</div>
          <div class="bar" data-entity="${escapeHtml(id)}">${spans}</div><div class="total">${data ? duration(total) : "…"}</div>`;
      })
      .join("");
    const marks = [0, 0.25, 0.5, 0.75, 1].map((f) => `<span>${escapeHtml(hourLabel(hass, x0 + f * span))}</span>`).join("");
    return `${this.title(hass, "activity")}<div class="tl">${rows}</div><div class="axis">${marks}</div>`;
  }
}

// ---------------------------------------------------------------------------
// Energy per day
// ---------------------------------------------------------------------------

/** The electricity entity with long-term statistics: the user's meter, else what CSNet records. */
function electricityEntity(unit) {
  return unit.meter_energy || unit.server_electricity_today;
}

class CsnetDailyEnergyCard extends CsnetBaseCard {
  static get minColumns() {
    return 6;
  }

  static editorSchema() {
    return [
      { name: "title", selector: { text: {} } },
      { name: "days", selector: { number: { min: 3, max: 90, step: 1, mode: "box" } } },
    ];
  }

  get days() {
    return Number(this._config.days ?? 14);
  }

  dataKey() {
    const unit = this.unit;
    const ids = [electricityEntity(unit), unit.server_heat_today, unit.outdoor].filter(Boolean);
    return ids.length ? `${ids.join("|")}|${this.days}` : null;
  }

  refreshMs() {
    return 30 * 60000;
  }

  async fetchData(hass) {
    const unit = this.unit;
    const start = startOfDay(Date.now() - (this.days - 1) * 86400000);
    const stats = await statistics(hass, [electricityEntity(unit), unit.server_heat_today, unit.outdoor], start, "day", ["change", "mean"]);
    const byDay = new Map();
    const day = (ms) => startOfDay(ms);
    const put = (id, key, field) => {
      for (const row of stats[id] || []) {
        if (!Number.isFinite(row[field])) continue;
        const entry = byDay.get(day(row.start)) || { at: day(row.start) };
        entry[key] = row[field];
        byDay.set(entry.at, entry);
      }
    };
    put(electricityEntity(unit), "electricity", "change");
    put(unit.server_heat_today, "heat", "change");
    put(unit.outdoor, "outdoor", "mean");
    return [...byDay.values()].sort((a, b) => a.at - b.at);
  }

  css() {
    return CHART_CSS;
  }

  content(hass) {
    const days = Array.isArray(this._data) ? this._data : [];
    const W = 600;
    const H = 230;
    const pad = { l: 36, r: 34, t: 18, b: 22 };
    const energies = days.flatMap((d) => [d.electricity, d.heat]).filter(Number.isFinite);
    const estep = niceStep(Math.max(...(energies.length ? energies : [10])));
    const emax = Math.max(estep, Math.ceil(Math.max(...(energies.length ? energies : [10])) / estep) * estep);
    const temps = days.map((d) => d.outdoor).filter(Number.isFinite);
    const [tmin, tmax] = niceRange(temps.length ? temps : [0, 10], 5, 1);
    const n = Math.max(days.length, 1);
    const slot = (W - pad.l - pad.r) / n;
    const bar = Math.min(16, slot / 2.6);
    const sy = (v) => H - pad.b - (v / emax) * (H - pad.t - pad.b);
    const st = (v) => H - pad.b - ((v - tmin) / (tmax - tmin || 1)) * (H - pad.t - pad.b);
    let svg = "";
    for (let v = 0; v <= emax + 1e-9; v += estep) {
      svg += `<line x1="${pad.l}" x2="${W - pad.r}" y1="${sy(v)}" y2="${sy(v)}" stroke="var(--csnet-line)" stroke-width=".6"/>
        <text x="${pad.l - 5}" y="${sy(v) + 3}" text-anchor="end" font-size="10" fill="var(--secondary-text-color)">${fmt(hass, v, 0)}</text>`;
    }
    for (let v = tmin; v <= tmax + 1e-9; v += 5) svg += `<text x="${W - pad.r + 5}" y="${st(v) + 3}" font-size="10" fill="var(--csnet-cool)">${fmt(hass, v, 0)}°</text>`;
    const outdoorPts = [];
    days.forEach((d, i) => {
      const cx = pad.l + slot * (i + 0.5);
      if (Number.isFinite(d.electricity)) svg += `<rect x="${cx - bar - 1}" y="${sy(d.electricity)}" width="${bar}" height="${Math.max(0, sy(0) - sy(d.electricity))}" rx="2" fill="var(--csnet-elec)"/>`;
      if (Number.isFinite(d.heat)) svg += `<rect x="${cx + 1}" y="${sy(d.heat)}" width="${bar}" height="${Math.max(0, sy(0) - sy(d.heat))}" rx="2" fill="var(--csnet-heat)" opacity=".85"/>`;
      if (d.heat > 0 && d.electricity > 0) {
        svg += `<text x="${cx}" y="${Math.min(sy(d.heat), sy(d.electricity)) - 4}" text-anchor="middle" font-size="9" fill="var(--csnet-ok)">${fmt(hass, d.heat / d.electricity, 1)}</text>`;
      }
      if (Number.isFinite(d.outdoor)) outdoorPts.push([cx, st(d.outdoor)]);
      if (n <= 16 || i % Math.ceil(n / 12) === 0) svg += `<text x="${cx}" y="${H - 6}" text-anchor="middle" font-size="10" fill="var(--secondary-text-color)">${escapeHtml(dayLabel(hass, d.at))}</text>`;
    });
    if (outdoorPts.length) {
      svg += `<path d="${outdoorPts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ")}" fill="none" stroke="var(--csnet-cool)" stroke-width="2"/>`;
      svg += outdoorPts.map((p) => `<circle cx="${p[0].toFixed(1)}" cy="${p[1].toFixed(1)}" r="2.5" fill="var(--csnet-cool)"/>`).join("");
    }
    const unit = this.unit;
    const items = [
      ["var(--csnet-elec)", `${t(hass, "electricity")} (kWh)`],
      ["var(--csnet-heat)", `${t(hass, "heat")} (kWh)`],
      ["var(--csnet-cool)", `${t(hass, "outdoor_mean")} (°C)`],
      ["var(--csnet-ok)", t(hass, "cop")],
    ];
    const note = unit.meter_energy ? "" : `<div class="note">${escapeHtml(t(hass, "electricity_source_server"))}</div>`;
    return `${this.title(hass, "daily_energy")}${legend(items)}<svg viewBox="0 0 ${W} ${H}" style="width:100%;display:block">${svg}</svg>${note}`;
  }
}

// ---------------------------------------------------------------------------
// Power today against the usual day
// ---------------------------------------------------------------------------

class CsnetPowerProfileCard extends CsnetBaseCard {
  static get minColumns() {
    return 6;
  }

  static editorSchema() {
    return [
      { name: "title", selector: { text: {} } },
      { name: "days", selector: { number: { min: 3, max: 60, step: 1, mode: "box" } } },
      { name: "power_entity", selector: { entity: { domain: "sensor", device_class: "power" } } },
    ];
  }

  get days() {
    return Number(this._config.days ?? 14);
  }

  dataKey() {
    return this.unit.power ? `${this.unit.power}|${this.days}` : null;
  }

  refreshMs() {
    return 5 * 60000;
  }

  async fetchData(hass) {
    const id = this.unit.power;
    const today = startOfDay();
    const [recent, past] = await Promise.all([
      statistics(hass, [id], today, "5minute", ["mean"]),
      statistics(hass, [id], today - this.days * 86400000, "hour", ["mean"], today),
    ]);
    const sums = new Array(24).fill(0);
    const counts = new Array(24).fill(0);
    for (const row of past[id] || []) {
      if (!Number.isFinite(row.mean)) continue;
      const hour = new Date(row.start).getHours();
      sums[hour] += row.mean;
      counts[hour] += 1;
    }
    return {
      today: (recent[id] || []).filter((r) => Number.isFinite(r.mean)).map((r) => [r.start, r.mean]),
      profile: sums.map((s, h) => (counts[h] ? s / counts[h] : null)),
    };
  }

  css() {
    return CHART_CSS;
  }

  content(hass) {
    const unit = this.unit;
    const data = this._data && !this._data.error ? this._data : { today: [], profile: [] };
    const x0 = startOfDay();
    const x1 = x0 + 86400000;
    const profile = data.profile
      .map((v, h) => [x0 + (h + 0.5) * 3600000, v])
      .filter((p) => Number.isFinite(p[1]));
    const values = [...data.today.map((p) => p[1]), ...profile.map((p) => p[1])];
    const pstep = niceStep(Math.max(...(values.length ? values : [1000])));
    const max = Math.max(pstep, Math.ceil(Math.max(...(values.length ? values : [1000])) / pstep) * pstep);
    const ticks = [0, 6, 12, 18, 24].map((h) => [x0 + h * 3600000, `${String(h).padStart(2, "0")}h`]);
    const chart = timeChart(hass, {
      x0,
      x1,
      series: [
        { points: profile, color: "var(--secondary-text-color)", width: 1.6, dash: "5 4" },
        { points: data.today, color: "var(--csnet-heat)", width: 1.8, fill: true },
      ],
      left: { min: 0, max, step: pstep, digits: 0 },
      ticks,
    });
    const hour = new Date().getHours();
    const usual = data.profile[hour];
    const now = num(hass, unit.power);
    const head = `<div class="headline-row">
      <div data-entity="${escapeHtml(unit.power)}"><div class="k">${t(hass, "now")}</div><div class="v" style="color:var(--csnet-heat)">${fmt(hass, now, 0)} W</div></div>
      <div><div class="k">${escapeHtml(t(hass, "usual_at_this_hour", { d: this.days }))}</div><div class="v">${fmt(hass, usual, 0)} W</div></div></div>`;
    const items = [
      ["var(--csnet-heat)", t(hass, "today")],
      ["var(--secondary-text-color)", t(hass, "average_profile", { d: this.days }), true],
    ];
    const source = unit.meter_power && unit.power === unit.meter_power ? friendly(hass, unit.power, unit.power) : null;
    const note = source ? t(hass, "power_from", { name: source }) : t(hass, "power_estimated");
    return `${this.title(hass, "power_profile")}${head}${legend(items)}${chart}<div class="note">${escapeHtml(note)}</div>`;
  }
}

// ---------------------------------------------------------------------------
// Energy signature and forecast
// ---------------------------------------------------------------------------

class CsnetEnergySignatureCard extends CsnetBaseCard {
  static editorSchema() {
    return [
      { name: "title", selector: { text: {} } },
      { name: "days", selector: { number: { min: 7, max: 365, step: 1, mode: "box" } } },
      { name: "weather_entity", selector: { entity: { domain: "weather" } } },
      { name: "price", selector: { number: { min: 0, max: 5, step: 0.001, mode: "box" } } },
      { name: "price_entity", selector: { entity: {} } },
    ];
  }

  get days() {
    return Number(this._config.days ?? 60);
  }

  watched() {
    return [...super.watched(), this._config.price_entity, ...priceEntities(this._data?.price)];
  }

  get weather() {
    return this._config.weather_entity || Object.keys(this._hass?.states || {}).find((id) => id.startsWith("weather."));
  }

  dataKey() {
    const unit = this.unit;
    const energy = electricityEntity(unit);
    return energy && unit.outdoor ? `${energy}|${unit.outdoor}|${unit.power || ""}|${this.weather || ""}|${this.days}` : null;
  }

  refreshMs() {
    return 60 * 60000;
  }

  async fetchData(hass) {
    const unit = this.unit;
    const energy = electricityEntity(unit);
    const today = startOfDay();
    const [daily, hourly, forecast, price] = await Promise.all([
      statistics(hass, [energy, unit.outdoor], today - this.days * 86400000, "day", ["change", "mean"], today),
      unit.power ? statistics(hass, [unit.power], today - 14 * 86400000, "hour", ["min"]) : Promise.resolve({}),
      loadForecast(hass, this.weather),
      loadEnergyPrice(hass),
    ]);
    const outdoorByDay = new Map((daily[unit.outdoor] || []).filter((r) => Number.isFinite(r.mean)).map((r) => [startOfDay(r.start), r.mean]));
    const points = (daily[energy] || [])
      .filter((r) => Number.isFinite(r.change) && r.change > 0 && outdoorByDay.has(startOfDay(r.start)))
      .map((r) => [outdoorByDay.get(startOfDay(r.start)), r.change, r.start]);
    const last7 = points.filter((p) => p[2] >= today - 7 * 86400000).map((p) => p[1]);
    const floors = (hourly[unit.power] || []).map((r) => r.min).filter((v) => Number.isFinite(v) && v > 0);
    const tomorrow = startOfDay(today + 36 * 3600000);
    const entry = (forecast || []).find((f) => startOfDay(toMs(f.datetime)) === tomorrow);
    const tomorrowMean = entry && Number.isFinite(entry.temperature) ? (entry.temperature + (Number.isFinite(entry.templow) ? entry.templow : entry.temperature)) / 2 : null;
    return {
      fit: regression(points.map((p) => [p[0], p[1]])),
      points,
      avg7: last7.length ? last7.reduce((a, b) => a + b, 0) / last7.length : null,
      floor: floors.length ? Math.min(...floors) : null,
      tomorrowMean,
      price,
    };
  }

  css() {
    return `
      .grid4 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px 12px; }
      .k { font-size: 10px; letter-spacing: .14em; text-transform: uppercase; color: var(--csnet-muted); }
      .v { font-size: 28px; font-weight: 700; line-height: 1.1; font-variant-numeric: tabular-nums; }
      .s { font-size: 11px; color: var(--csnet-muted); }
    `;
  }

  price(hass) {
    const own = configuredPrice(hass, this._config);
    return own !== undefined ? own : priceValue(hass, this._data?.price);
  }

  content(hass) {
    if (!electricityEntity(this.unit) || !this.unit.outdoor) return `${this.title(hass, "energy_signature")}<div class="message">${escapeHtml(t(hass, "needs_meter"))}</div>`;
    const d = this._data;
    if (!d || d.error) return `${this.title(hass, "energy_signature")}<div class="message">${escapeHtml(d?.error ? t(hass, "not_enough_history") : t(hass, "loading"))}</div>`;
    const price = this.price(hass);
    const money = (kwh) => (price !== null && Number.isFinite(kwh) ? ` · ≈ ${fmt(hass, kwh * price, 2)} ${escapeHtml(hass.config?.currency || "€")}` : "");
    const fit = d.fit && d.fit.n >= 7 ? d.fit : null;
    const predicted = fit && d.tomorrowMean !== null ? Math.max(0, fit.a + fit.b * d.tomorrowMean) : null;
    const cell = (k, v, s, color) => `<div><div class="k">${escapeHtml(k)}</div><div class="v" style="${color ? `color:${color}` : ""}">${v}</div><div class="s">${s}</div></div>`;
    const cells = [
      cell(
        t(hass, "tomorrow_weather"),
        predicted !== null ? `≈ ${fmt(hass, predicted, 1)} kWh` : "–",
        predicted !== null ? `${escapeHtml(t(hass, "mean_outdoor", { v: fmt(hass, d.tomorrowMean, 1) }))}${money(predicted)}` : escapeHtml(t(hass, this.weather ? "no_forecast" : "no_weather")),
        "var(--csnet-heat)",
      ),
      cell(t(hass, "average_7_days"), d.avg7 !== null ? `${fmt(hass, d.avg7, 1)} kWh` : "–", `${escapeHtml(t(hass, "per_day"))}${money(d.avg7)}`),
      cell(
        t(hass, "per_degree"),
        fit ? `+${fmt(hass, Math.abs(fit.b), 1)} kWh` : "–",
        fit ? escapeHtml(t(hass, "fit_quality", { r: fmt(hass, fit.r2 * 100, 0), n: fit.n })) : escapeHtml(t(hass, "not_enough_history")),
        "var(--csnet-cool)",
      ),
      cell(t(hass, "base_load"), d.floor !== null ? `${fmt(hass, d.floor, 0)} W` : "–", escapeHtml(t(hass, "base_load_detail"))),
    ];
    return `${this.title(hass, "energy_signature")}<div class="grid4">${cells.join("")}</div><div class="note">${escapeHtml(t(hass, "signature_note", { d: this.days }))}</div>`;
  }
}

// ---------------------------------------------------------------------------
// Editor (shared): Home Assistant's own form element
// ---------------------------------------------------------------------------

const LANGUAGE_FIELD = {
  name: "language",
  selector: {
    select: {
      mode: "dropdown",
      options: [
        { value: "auto", label: "Auto" },
        { value: "en", label: "English" },
        { value: "fr", label: "Français" },
        { value: "es", label: "Español" },
      ],
    },
  },
};

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
  ["csnet-temperatures-card", CsnetTemperaturesCard, "CSNet · Temperatures", "Flow, return, target, outdoor temperature and compressor frequency over the last hours."],
  ["csnet-activity-card", CsnetActivityCard, "CSNet · Activity", "What ran over the last hours: compressor, defrost, circuit demands, hot water, pumps, backup heater."],
  ["csnet-daily-energy-card", CsnetDailyEnergyCard, "CSNet · Energy per day", "Electricity and heat per day with the COP and the average outdoor temperature."],
  ["csnet-power-profile-card", CsnetPowerProfileCard, "CSNet · Power today", "Today's power against the average day of the last two weeks."],
  ["csnet-energy-signature-card", CsnetEnergySignatureCard, "CSNet · Energy signature", "Tomorrow's electricity from the weather forecast, kWh per degree, 7-day average and base load."],
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
