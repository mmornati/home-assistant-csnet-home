/* Presentation of the Hitachi CSNet Home integration (see ../engine/engine.js and the canvas-video skill).
 *
 * Each scene is fn(t, d, cues): t = local time in seconds, d = scene duration,
 * cues = the spoken sentences [{s, e, text}] from timing.js. Animations hang on
 * at(cues, i), so they follow the voice in every language. Pure functions of t.
 *
 * The screenshots are the bundled dashboard cards on a test instance connected to
 * a real Yutaki S with two circuits (no demo data). The heating curve values are
 * that unit's: C1 by points (60 °C at -10 °C, 21 °C at 20 °C), C2 gradient 0.6.
 */
"use strict";

const IMG = "img/";
const SHOTS = {
  water: "card-water-circuit-dark.jpg",
  heatpump: "card-heat-pump-dark.jpg",
  curve: "card-heating-curve-dark.jpg",
  performance: "card-performance-dark.jpg",
  health: "card-system-health-dark.jpg",
  refrigerant: "card-refrigerant-dark.jpg",
  temperatures: "card-temperatures-dark.jpg",
  activity: "card-activity-dark.jpg",
  daily: "card-daily-energy-dark.jpg",
  power: "card-power-profile-dark.jpg",
  signature: "card-energy-signature-dark.jpg",
  mark: "mark.svg",
};
// The cards speak the video's language: French screenshots in img/fr/
const IMAGES = { en: {}, fr: {} };
const imagesReady = Promise.all(
  ["en", "fr"].flatMap((lang) =>
    Object.entries(SHOTS).map(
      ([key, file]) =>
        new Promise((resolve) => {
          const img = new Image();
          img.onload = img.onerror = () => resolve();
          img.src = IMG + (lang === "fr" && key !== "mark" ? "fr/" : "") + file;
          IMAGES[lang][key] = img;
        }),
    ),
  ),
);
const shot = (key) => (IMAGES[LANG] || IMAGES.en)[key];

/* A headline at the largest size (up to `size`) that fits between x = 80 and 1200. */
function fitHeadline(s, k, y, size) {
  let z = size;
  while (z > 26 && measure(s, z, 800, SORA) > 1120) z -= 2;
  headline(s, k, y, z);
}

/* Thermal palette of the project site (DESIGN.md). */
const IRONBOW = ["#07040f", "#1d0a3a", "#470f76", "#8b2185", "#c5376f", "#ea5a3a", "#f7922a", "#ffd24a", "#fff8e6"];
const HEAT = "#f7922a", EMBER = "#ea5a3a", AMBER = "#ffd24a", ICE = "#9ee3ff", GREEN = "#7bd88f";

const STR = {
  en: {
    k1: "HOME ASSISTANT · OPEN SOURCE",
    h1: "Your Hitachi heat pump, in Home Assistant.",
    unit: "Yutaki / Yutampo", module: "ATW-IOT-01", cloud: "CSNet Manager", ha: "Home Assistant",
    k2: "SET UP", h2: "Sign in once. Everything appears.",
    s1: "Install from HACS", s2: "Sign in with CSNet", s3: "Entities appear",
    e1: "climate · one per zone", e2: "water_heater · hot water, pool", e3: "sensor · water loop, compressor, energy",
    e4: "binary_sensor · what runs", e5: "number · fixed water temperature",
    k3: "LIVE", h3: "See the unit at work.",
    real: "Bundled card on a real Yutaki S, two circuits",
    k4: "HEATING CURVES", h4: "Describe the water law once.",
    fromCsnet: "From CSNet: C1 Points · C2 Gradient · values unknown",
    form: "Configure · Heating curves", f1: "C1 low ambient", f2: "C1 water at low ambient", f3: "C1 high ambient", f4: "C1 water at high ambient", f5: "C2 gradient",
    outdoor: "outdoor °C", water: "water °C", unitTarget: "unit target 40 °C", now: "now, 3 °C outside",
    k5: "REAL COP", h5: "Your meter, a real COP.",
    heat: "heat (CSNet)", elec: "electricity (your meter)", cond: "13 November 2026 · Yutaki S · three-phase meter",
    cost: "Cost of each day", forecast: "Tomorrow, from the weather forecast", price: "Energy dashboard price",
    k6: "DASHBOARD", h6: "Eleven cards. Nothing else to install.",
    search: "Search “CSNet”", p1: "finds its entities", p2: "light and dark", p3: "English · Français · Español",
    k7: "OPEN SOURCE", h7: "Unofficial, by necessity. Open, by choice.",
    site: "mmornati.github.io/home-assistant-csnet-home",
    legal: "Independent project, not affiliated with Hitachi · Apache License 2.0",
    docs: "Documentation · Dashboard cards · Release notes",
  },
  fr: {
    k1: "HOME ASSISTANT · OPEN SOURCE",
    h1: "Votre pompe à chaleur Hitachi, dans Home Assistant.",
    unit: "Yutaki / Yutampo", module: "ATW-IOT-01", cloud: "CSNet Manager", ha: "Home Assistant",
    k2: "INSTALLATION", h2: "Connectez-vous une fois. Tout apparaît.",
    s1: "Installer avec HACS", s2: "Se connecter à CSNet", s3: "Les entités apparaissent",
    e1: "climate · une par zone", e2: "water_heater · eau chaude, piscine", e3: "sensor · circuit d'eau, compresseur, énergie",
    e4: "binary_sensor · ce qui tourne", e5: "number · température d'eau fixe",
    k3: "EN DIRECT", h3: "Voir l'unité en marche.",
    real: "Carte fournie, sur une vraie Yutaki S à deux circuits",
    k4: "LOIS D'EAU", h4: "Décrivez la loi d'eau une fois.",
    fromCsnet: "Depuis CSNet : C1 Points · C2 Pente · valeurs inconnues",
    form: "Configurer · Lois d'eau", f1: "C1 extérieur bas", f2: "C1 eau à extérieur bas", f3: "C1 extérieur haut", f4: "C1 eau à extérieur haut", f5: "C2 pente",
    outdoor: "extérieur °C", water: "eau °C", unitTarget: "consigne de l'unité 40 °C", now: "maintenant, 3 °C dehors",
    k5: "VRAI COP", h5: "Votre compteur, un vrai COP.",
    heat: "chaleur (CSNet)", elec: "électricité (votre compteur)", cond: "13 novembre 2026 · Yutaki S · compteur triphasé",
    cost: "Coût de chaque jour", forecast: "Demain, d'après la météo", price: "Prix du tableau Énergie",
    k6: "TABLEAU DE BORD", h6: "Onze cartes. Rien d'autre à installer.",
    search: "Chercher « CSNet »", p1: "trouve ses entités", p2: "clair et sombre", p3: "English · Français · Español",
    k7: "OPEN SOURCE", h7: "Non officiel par nécessité. Ouvert par choix.",
    site: "mmornati.github.io/home-assistant-csnet-home",
    legal: "Projet indépendant, sans lien avec Hitachi · Licence Apache 2.0",
    docs: "Documentation · Cartes · Notes de version",
  },
};

/* Background: night of a thermal camera, a slow warm bloom low on the frame. */
function thermalBackground(t) {
  ctx.fillStyle = "#0b0712";
  ctx.fillRect(0, 0, W, H);
  const x = 900 + Math.sin(t * 0.13) * 120, y = 640 + Math.cos(t * 0.11) * 30;
  const g = ctx.createRadialGradient(x, y, 20, x, y, 720);
  g.addColorStop(0, "rgba(234, 90, 58, 0.30)");
  g.addColorStop(0.4, "rgba(139, 33, 133, 0.16)");
  g.addColorStop(1, "rgba(11, 7, 18, 0)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);
  // ironbow scale on the left edge, like the site's hero
  const s = ctx.createLinearGradient(0, H - 40, 0, 40);
  IRONBOW.forEach((c, i) => s.addColorStop(i / (IRONBOW.length - 1), c));
  ctx.globalAlpha = 0.55;
  ctx.fillStyle = s;
  ctx.fillRect(28, 60, 4, H - 140);
  ctx.globalAlpha = 1;
}

function drawShot(key, x, y, w, alpha = 1) {
  const img = shot(key);
  if (!img || !img.naturalWidth) return 0;
  const h = (w * img.naturalHeight) / img.naturalWidth;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.shadowColor = "rgba(0,0,0,.55)";
  ctx.shadowBlur = 30;
  rr(x, y, w, h, 12);
  ctx.clip();
  ctx.drawImage(img, x, y, w, h);
  ctx.restore();
  return h;
}

function fitShot(key, cx, cy, maxW, maxH, alpha, scale = 1) {
  const img = shot(key);
  if (!img || !img.naturalWidth) return;
  const r = Math.min(maxW / img.naturalWidth, maxH / img.naturalHeight) * scale;
  const w = img.naturalWidth * r, h = img.naturalHeight * r;
  drawShot(key, cx - w / 2, cy - h / 2, w, alpha);
}

/* 1 · intro */
function sIntro(t, d, cues) {
  kicker(S.k1, seg(t, 0.1, 0.6));
  fitHeadline(S.h1, seg(t, 0.2, 0.9), 150, 50);
  const nodes = [
    [S.unit, 210, HEAT],
    [S.cloud, 640, ICE],
    [S.ha, 1070, AMBER],
  ];
  const y = 400;
  nodes.forEach(([label, x, color], i) => {
    const k = outBack(seg(t, 0.6 + i * 0.35, 1.2 + i * 0.35));
    if (k <= 0) return;
    panel(x - 130 * k, y - 60, 260 * k, 120, { r: 10, fill: "#140c22", stroke: color, lw: 2 });
    text(label, x, y + 8, { size: 24, weight: 700, font: SORA, color: "#fff6d6", align: "center", alpha: seg(t, 1 + i * 0.35, 1.4 + i * 0.35) });
  });
  const k1 = seg(t, 1.8, 2.6);
  arrow(340, y, 510, y, k1, HEAT);
  pill(S.module, 425, y - 46, { align: "center", size: 14, font: MONO, color: HEAT, fill: "#140c22", stroke: HEAT });
  const a1 = at(cues, 1, 4);
  arrow(770, y, 940, y, seg(t, a1, a1 + 0.7), AMBER);
  if (t > a1 + 0.7) packets(770, y, 940, y, t, { n: 3, period: 1.4, color: AMBER, r: 5 });
  if (t > 2.6) packets(340, y, 510, y, t, { n: 3, period: 1.4, color: HEAT, r: 5 });
}

/* 2 · setup */
function sSetup(t, d, cues) {
  kicker(S.k2, seg(t, 0.1, 0.6));
  fitHeadline(S.h2, seg(t, 0.2, 0.9), 150, 46);
  [S.s1, S.s2, S.s3].forEach((s, i) => {
    const k = seg(t, 0.6 + i * 0.6, 1.1 + i * 0.6);
    panel(80 + i * 380, 210, 340, 70, { r: 8, fill: "#140c22", stroke: i === 2 ? AMBER : "#3b2a55", lw: 1.5, alpha: k });
    text(`${i + 1}`, 110 + i * 380, 255, { size: 28, weight: 800, font: SORA, color: AMBER, alpha: k });
    text(s, 150 + i * 380, 252, { size: 20, weight: 600, font: INTER, color: "#fff6d6", alpha: k });
  });
  const a1 = at(cues, 1, 3.5);
  [S.e1, S.e2, S.e3, S.e4, S.e5].forEach((e, i) => {
    const k = seg(t, a1 + i * 0.35, a1 + 0.5 + i * 0.35);
    dot(108, 342 + i * 52, 7, IRONBOW[4 + (i % 5)], k);
    text(e, 130, 349 + i * 52, { size: 22, font: MONO, color: "#fff6d6", alpha: k });
  });
}

/* 3 · live water circuit (real screenshot) */
function sLive(t, d, cues) {
  kicker(S.k3, seg(t, 0.1, 0.6));
  fitHeadline(S.h3, seg(t, 0.2, 0.9), 132, 42);
  const x = 140, y = 168, w = 1000;
  const h = drawShot("water", x, y, w, seg(t, 0.3, 1.0)) || 464;
  const box = (fx0, fy0, fx1, fy1) => [x + fx0 * w, y + fy0 * h, (fx1 - fx0) * w, (fy1 - fy0) * h];
  const a1 = at(cues, 1, 3), a2 = at(cues, 2, 5.5);
  if (t > a1 && t < a2 + 0.2) {
    highlight(...box(0.03, 0.26, 0.26, 0.66), seg(t, a1, a1 + 0.5), HEAT);
    highlight(...box(0.71, 0.14, 0.98, 0.73), seg(t, a1 + 1.2, a1 + 1.7), AMBER);
  }
  if (t > a2) {
    highlight(...box(0.56, 0.48, 0.68, 0.68), seg(t, a2, a2 + 0.5), GREEN);
    highlight(...box(0.01, 0.78, 0.94, 0.9), seg(t, a2 + 0.8, a2 + 1.3), ICE);
  }
  text(S.real, x, y + h + 26, { size: 13, font: MONO, color: "rgba(255,238,214,.6)", alpha: seg(t, 1, 1.5) });
}

/* 4 · heating curves, drawn from the unit's real settings */
function sCurve(t, d, cues) {
  kicker(S.k4, seg(t, 0.1, 0.6));
  fitHeadline(S.h4, seg(t, 0.2, 0.9), 132, 42);
  const gx = 540, gy = 210, gw = 660, gh = 360;
  const sx = (v) => gx + ((v + 20) / 45) * gw, sy = (v) => gy + gh - ((v - 15) / 50) * gh;
  const ka = seg(t, 0.4, 1.2);
  ctx.save();
  ctx.globalAlpha = ka;
  ctx.strokeStyle = "rgba(255,246,214,.14)";
  ctx.lineWidth = 1;
  for (let v = -20; v <= 25; v += 5) {
    ctx.beginPath(); ctx.moveTo(sx(v), gy); ctx.lineTo(sx(v), gy + gh); ctx.stroke();
    text(`${v}°`, sx(v), gy + gh + 20, { size: 12, font: MONO, color: "rgba(255,238,214,.6)", align: "center" });
  }
  for (let v = 20; v <= 60; v += 10) {
    ctx.beginPath(); ctx.moveTo(gx, sy(v)); ctx.lineTo(gx + gw, sy(v)); ctx.stroke();
    text(`${v}°`, gx - 8, sy(v) + 4, { size: 12, font: MONO, color: "rgba(255,238,214,.6)", align: "right" });
  }
  ctx.restore();
  text(S.outdoor, gx + gw, gy + gh + 42, { size: 12, font: MONO, color: "rgba(255,238,214,.6)", align: "right", alpha: ka });
  text(S.water, gx, gy - 12, { size: 12, font: MONO, color: "rgba(255,238,214,.6)", alpha: ka });

  text(S.fromCsnet, 80, 178, { size: 15, font: MONO, color: ICE, alpha: seg(t, 0.8, 1.4) });

  const a1 = at(cues, 1, 4);
  const kf = seg(t, a1, a1 + 0.4);
  panel(80, 240, 400, 270, { r: 8, fill: "#140c22", stroke: "#3b2a55", lw: 1.5, alpha: kf });
  text(S.form, 100, 272, { size: 16, weight: 700, font: INTER, color: AMBER, alpha: kf });
  [[S.f1, "-10 °C"], [S.f2, "60 °C"], [S.f3, "20 °C"], [S.f4, "21 °C"], [S.f5, "0.6"]].forEach(([label, value], i) => {
    const kv = seg(t, a1 + 0.3 + i * 0.25, a1 + 0.8 + i * 0.25);
    text(label, 100, 312 + i * 40, { size: 15, font: INTER, color: "rgba(255,238,214,.75)", alpha: kf });
    text(typed(value, kv), 455, 312 + i * 40, { size: 16, font: MONO, color: "#fff6d6", align: "right", alpha: kf });
  });

  const a2 = at(cues, 2, 6.5);
  const c1 = [[-20, 60], [-10, 60], [20, 21], [25, 21]].map(([o, w]) => [sx(o), sy(w)]);
  const c2 = [[-20, 44], [20, 20], [25, 20]].map(([o, w]) => [sx(o), sy(w)]);
  const kc = outCubic(seg(t, a2, a2 + 1.4));
  if (kc > 0) {
    line(partial(c1, kc), HEAT, 4);
    line(partial(c2, kc), GREEN, 4);
    text("C1", sx(-17), sy(60) - 12, { size: 16, weight: 700, font: SORA, color: HEAT, alpha: kc });
    text("C2", sx(-17), sy(42) - 12, { size: 16, weight: 700, font: SORA, color: GREEN, alpha: kc });
  }
  const km = outBack(seg(t, a2 + 1.4, a2 + 2));
  if (km > 0) {
    dot(sx(3), sy(43.1), 8 * km, HEAT);
    dot(sx(3), sy(30.2), 8 * km, GREEN);
    ring(sx(3), sy(40), 11 * km, "#fff6d6", 2.5);
    text(`${(43.1).toLocaleString(LANG)}°`, sx(3) + 14, sy(43.1) - 8, { size: 14, font: MONO, color: HEAT, alpha: km });
    text(`${(30.2).toLocaleString(LANG)}°`, sx(3) + 14, sy(30.2) + 18, { size: 14, font: MONO, color: GREEN, alpha: km });
    callout(S.unitTarget, sx(3) + 120, sy(40) + 60, sx(3) + 8, sy(40) + 8, seg(t, a2 + 2, a2 + 2.6));
    text(S.now, sx(3), gy + 14, { size: 12, font: MONO, color: "rgba(255,238,214,.7)", align: "center", alpha: km });
  }
}

/* 5 · real COP */
function sEnergy(t, d, cues) {
  kicker(S.k5, seg(t, 0.1, 0.6));
  fitHeadline(S.h5, seg(t, 0.2, 0.9), 132, 42);
  const a1 = at(cues, 1, 3.5), a2 = at(cues, 2, 8);
  const max = 110, bx = 120, bw = 620;
  const kh = outCubic(seg(t, a1, a1 + 1.2)), ke = outCubic(seg(t, a1 + 0.6, a1 + 1.8));
  if (t > a1) {
    panel(bx, 230, (bw * 99 / max) * kh, 46, { r: 6, fill: HEAT, stroke: false });
    text(`${Math.round(99 * kh)} kWh`, bx + (bw * 99 / max) * kh + 14, 262, { size: 24, weight: 700, font: SORA, color: HEAT });
    text(S.heat, bx, 220, { size: 15, font: MONO, color: "rgba(255,238,214,.75)" });
    panel(bx, 330, (bw * 40.7 / max) * ke, 46, { r: 6, fill: "#8e6bd8", stroke: false });
    text(`${(40.7 * ke).toLocaleString(LANG, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} kWh`, bx + (bw * 40.7 / max) * ke + 14, 362, { size: 24, weight: 700, font: SORA, color: "#b9a2f0", alpha: seg(t, a1 + 0.6, a1 + 1) });
    text(S.elec, bx, 320, { size: 15, font: MONO, color: "rgba(255,238,214,.75)", alpha: seg(t, a1 + 0.6, a1 + 1) });
    const kc = seg(t, a1 + 1.8, a1 + 3);
    text("COP", 1010, 240, { size: 20, font: MONO, color: GREEN, align: "center", alpha: kc });
    text((2.43 * outCubic(kc)).toLocaleString(LANG, { minimumFractionDigits: 2, maximumFractionDigits: 2 }), 1010, 340, { size: 104, weight: 800, font: SORA, color: GREEN, align: "center", alpha: kc });
    text(S.cond, bx, 420, { size: 13, font: MONO, color: "rgba(255,238,214,.55)", alpha: seg(t, a1 + 1.5, a1 + 2) });
  }
  let px = 120;
  [S.cost, S.forecast, S.price].forEach((s, i) => {
    const k = seg(t, a2 + i * 0.4, a2 + 0.5 + i * 0.4);
    px += pill(s, px, 500, { size: 18, color: "#fff6d6", fill: "#140c22", stroke: [AMBER, ICE, HEAT][i], alpha: k }) + 18;
  });
}

/* 6 · eleven cards */
function sCards(t, d, cues) {
  kicker(S.k6, seg(t, 0.1, 0.6));
  fitHeadline(S.h6, seg(t, 0.2, 0.9), 132, 42);
  const order = ["heatpump", "water", "curve", "performance", "health", "refrigerant", "temperatures", "activity", "daily", "power", "signature"];
  const cols = 4, cw = 262, ch = 128, x0 = 95, y0 = 172, gap = 12;
  order.forEach((key, i) => {
    const k = outBack(seg(t, 0.5 + i * 0.12, 1.0 + i * 0.12));
    const cx = x0 + (i % cols) * (cw + gap) + cw / 2, cy = y0 + Math.floor(i / cols) * (ch + gap) + ch / 2;
    if (k > 0) fitShot(key, cx, cy, cw, ch, Math.min(1, k), 0.6 + 0.4 * k);
  });
  const a1 = at(cues, 1, 3), a2 = at(cues, 2, 5);
  const ks = seg(t, a1, a1 + 0.5);
  if (ks > 0) {
    const sw = cw, sx0 = x0 + 3 * (cw + gap), sy0 = y0 + 2 * (ch + gap) + ch / 2 - 27;
    panel(sx0, sy0, sw, 54, { r: 27, fill: "#140c22", stroke: AMBER, lw: 2, alpha: ks });
    text(typed(S.search, seg(t, a1 + 0.2, a1 + 1.4)), sx0 + 20, sy0 + 33, { size: 14, font: INTER, color: "#fff6d6", alpha: ks });
  }
  let px = 95;
  [S.p1, S.p2, S.p3].forEach((s, i) => {
    px += 16 + pill(s, px, 620, { size: 16, color: "#fff6d6", fill: "#140c22", stroke: [GREEN, ICE, AMBER][i], alpha: seg(t, a2 + i * 0.5, a2 + 0.5 + i * 0.5) });
  });
}

/* 7 · outro */
function sOutro(t, d, cues) {
  kicker(S.k7, seg(t, 0.1, 0.6));
  const km = outBack(seg(t, 0.2, 0.9));
  const img = shot("mark");
  if (img && img.naturalWidth && km > 0) {
    ctx.save(); ctx.globalAlpha = Math.min(1, km);
    ctx.drawImage(img, 80, 120, 110 * km, 110 * km);
    ctx.restore();
  }
  fitHeadline(S.h7, seg(t, 0.4, 1.1), 300, 46);
  text(S.legal, 80, 352, { size: 18, font: INTER, color: "rgba(255,238,214,.75)", alpha: seg(t, 0.8, 1.4) });
  const a1 = at(cues, 1, 3);
  const k = seg(t, a1, a1 + 0.6);
  panel(80, 420, 760, 64, { r: 4, fill: AMBER, stroke: false, alpha: k });
  text(S.site, 104, 461, { size: 24, weight: 600, font: MONO, color: "#0b0712", alpha: k });
  text(S.docs, 80, 520, { size: 18, font: INTER, color: "#fff6d6", alpha: seg(t, a1 + 0.5, a1 + 1) });
}

window.videoReady = imagesReady.then(() => {
  VIDEO.create({
    title: { en: "Hitachi CSNet Home for Home Assistant", fr: "Hitachi CSNet Home pour Home Assistant" },
    kicker: { en: "A one-minute tour", fr: "La visite en une minute" },
    langs: ["en", "fr"],
    theme: {
      bg: "#0b0712", bg2: "#140c22", panel: "#140c22", panel2: "#1d0a3a", line: "#3b2a55",
      ink: "#fff6d6", soft: "rgba(255,238,214,.74)", faint: "rgba(255,238,214,.5)",
      accent: AMBER, accent2: EMBER, good: GREEN, warn: AMBER, bad: EMBER, deep: "#1d0a3a",
    },
    strings: STR,
    background: thermalBackground,
    poster: "curve",
    scenes: { intro: sIntro, setup: sSetup, live: sLive, curve: sCurve, energy: sEnergy, cards: sCards, outro: sOutro },
  });
  return window.videoReady;
});
