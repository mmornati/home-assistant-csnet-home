/* Thermogram hero: a house cross-section rendered as a thermal image.
   The field is synthetic (an illustration); the span auto-ranges per hvac mode. */
(() => {
  const root = document.querySelector("[data-thermo]");
  if (!root) return;

  const canvas = root.querySelector("canvas");
  const ctx = canvas.getContext("2d", { alpha: false });
  const meter = root.querySelector("[data-meter]");
  const out = {
    zone: root.querySelector("[data-meter-zone]"),
    temp: root.querySelector("[data-meter-temp]"),
    entity: root.querySelector("[data-meter-entity]"),
    state: root.querySelector("[data-meter-state]"),
  };
  const card = root.querySelector(".tx-meter__card");
  const scaleMark = root.querySelector("[data-scale-mark]");
  const scaleValue = root.querySelector("[data-scale-value]");
  const modeButtons = root.querySelectorAll("[data-mode]");
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // The camera auto-ranges like a real one: level and span follow the scene.
  const SPAN = { heat: [-5, 55], cool: [12, 46] };
  let T_MIN = SPAN.heat[0];
  let T_MAX = SPAN.heat[1];
  const scaleEnds = root.querySelectorAll(".tx-scale__end");

  // Ironbow, as thermal cameras ship it.
  const STOPS = [
    [0.0, "#07040f"], [0.14, "#1d0a3a"], [0.3, "#470f76"], [0.45, "#8b2185"],
    [0.58, "#c5376f"], [0.7, "#ea5a3a"], [0.81, "#f7922a"], [0.91, "#ffd24a"], [1.0, "#fff8e6"],
  ];
  const LUT = buildLut(STOPS);

  const MODES = {
    heat: {
      outside: 2, soil: 7, interior: 23, c1: 34, emitter: 50, dhw: 52, odu: -3,
      roof: 8.5, window: 10.5, pipe: 42, pulse: 4,
    },
    cool: {
      outside: 36, soil: 19, interior: 22, c1: 18, emitter: 8, dhw: 50, odu: 52,
      roof: 40, window: 30, pipe: 8, pulse: -4,
    },
  };

  // Scene geometry in scene units (u: 0..1 across, v: 0..1 down).
  const HOUSE = { u0: 0.08, u1: 0.74, v0: 0.26, v1: 0.84, slab: 0.55 };
  const ROOF = { peak: [0.41, 0.05], left: [0.03, 0.27], right: [0.79, 0.27] };
  const TANK = { u0: 0.585, u1: 0.655, v0: 0.6, v1: 0.82 };
  const ODU = { u0: 0.82, u1: 0.96, v0: 0.66, v1: 0.84 };
  const PIPE = [[0.655, 0.8], [0.74, 0.8], [0.82, 0.8]];
  const FLOOR = [[0.1, 0.822], [0.72, 0.822]];

  const ZONES = [
    {
      id: "dhw", hit: (u, v) => inside(u, v, TANK),
      label: "Hot water tank", entity: "water_heater.yutaki_dhw",
      state: () => "operation_mode: eco · target 50 °C",
      poi: [0.62, 0.71],
    },
    {
      id: "c2", hit: (u, v) => u > HOUSE.u0 && u < HOUSE.u1 && v > HOUSE.v0 && v < HOUSE.slab,
      label: "First floor · circuit C2", entity: "climate.yutaki_first_floor",
      state: (m) => (m === "heat" ? "hvac_action: heating · target 21 °C" : "hvac_action: cooling · target 24 °C"),
      poi: [0.3, 0.41],
    },
    {
      id: "c1", hit: (u, v) => u > HOUSE.u0 && u < HOUSE.u1 && v >= HOUSE.slab && v < HOUSE.v1,
      label: "Ground floor · circuit C1", entity: "climate.yutaki_ground_floor",
      state: (m) => (m === "heat" ? "underfloor · hvac_action: heating" : "underfloor · hvac_action: cooling"),
      poi: [0.3, 0.75],
    },
    {
      id: "odu", hit: (u, v) => inside(u, v, ODU),
      label: "Outdoor unit", entity: "sensor.yutaki_compressor_frequency",
      state: (m) => (m === "heat" ? "compressor running · defrost off" : "compressor running · rejecting heat"),
      poi: [0.89, 0.75],
    },
    {
      id: "attic", hit: (u, v) => v <= HOUSE.v0 && underRoof(u, v),
      label: "Attic", entity: null,
      state: () => "no zone here · nothing to control",
      poi: [0.41, 0.19],
    },
    {
      id: "soil", hit: (u, v) => v >= HOUSE.v1,
      label: "Ground", entity: null,
      state: () => "no sensor · not reported",
      poi: [0.3, 0.93],
    },
    {
      id: "outside", hit: () => true,
      label: "Outside air", entity: "sensor.yutaki_external_temperature",
      state: (m) => (m === "heat" ? "winter morning" : "summer afternoon"),
      poi: [0.9, 0.35],
    },
  ];
  const TOUR_WIDE = ["c1", "dhw", "c2", "odu", "outside"];
  const TOUR_NARROW = ["c1", "dhw", "c2", "odu"];
  let TOUR = TOUR_WIDE;

  let W = 0, H = 0, cols = 0, rows = 0, dpr = 1;
  let box = { x: 0, y: 0, w: 1, h: 1 };
  let baseHeat, baseCool, frame, off, offCtx, img;
  let mode = "heat";
  let mix = 0, mixFrom = 0, mixTo = 0, mixStart = 0;
  let spot = null; // {x, y} in CSS px
  let lastPointer = -Infinity;
  let tourIndex = 0, tourStart = 0, tourFrom = null;
  let visible = true;
  let raf = 0;

  function buildLut(stops) {
    const lut = new Uint8ClampedArray(256 * 3);
    const rgb = stops.map(([p, hex]) => [p, parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16)]);
    for (let i = 0; i < 256; i++) {
      const t = i / 255;
      let k = 0;
      while (k < rgb.length - 2 && t > rgb[k + 1][0]) k++;
      const a = rgb[k], b = rgb[k + 1];
      const f = (t - a[0]) / (b[0] - a[0] || 1);
      lut[i * 3] = a[1] + (b[1] - a[1]) * f;
      lut[i * 3 + 1] = a[2] + (b[2] - a[2]) * f;
      lut[i * 3 + 2] = a[3] + (b[3] - a[3]) * f;
    }
    return lut;
  }

  function inside(u, v, r) {
    return u > r.u0 && u < r.u1 && v > r.v0 && v < r.v1;
  }

  function underRoof(u, v) {
    const [px, py] = ROOF.peak;
    const [lx, ly] = ROOF.left;
    const [rx] = ROOF.right;
    if (u < lx || u > rx || v < py) return false;
    const edge = u < px ? py + ((px - u) / (px - lx)) * (ly - py) : py + ((u - px) / (rx - px)) * (ly - py);
    return v >= edge;
  }

  function segDist2(u, v, a, b) {
    const dx = b[0] - a[0], dy = b[1] - a[1];
    const len = dx * dx + dy * dy || 1e-9;
    let t = ((u - a[0]) * dx + (v - a[1]) * dy) / len;
    t = t < 0 ? 0 : t > 1 ? 1 : t;
    const ex = u - (a[0] + t * dx), ey = v - (a[1] + t * dy);
    return ex * ex + ey * ey;
  }

  function sources(m) {
    const p = MODES[m];
    const list = [
      { a: FLOOR[0], b: FLOOR[1], s: 0.03, t: p.c1 },
      { a: [TANK.u0 + 0.035, TANK.v0 + 0.03], b: [TANK.u0 + 0.035, TANK.v1 - 0.02], s: 0.03, t: p.dhw },
      { a: [ODU.u0 + 0.03, 0.75], b: [ODU.u1 - 0.03, 0.75], s: 0.04, t: p.odu },
      { a: PIPE[0], b: PIPE[1], s: 0.01, t: p.pipe },
      { a: PIPE[1], b: PIPE[2], s: 0.01, t: p.pipe },
      { a: ROOF.left, b: ROOF.peak, s: 0.014, t: p.roof },
      { a: ROOF.peak, b: ROOF.right, s: 0.014, t: p.roof },
      { a: [HOUSE.u0, 0.33], b: [HOUSE.u0, 0.45], s: 0.014, t: p.window },
      { a: [HOUSE.u0, 0.62], b: [HOUSE.u0, 0.74], s: 0.014, t: p.window },
      { a: [HOUSE.u1, 0.33], b: [HOUSE.u1, 0.45], s: 0.014, t: p.window },
    ];
    if (m === "heat") {
      // Radiators on circuit C2.
      list.push({ a: [0.115, 0.44], b: [0.115, 0.52], s: 0.02, t: p.emitter });
      list.push({ a: [0.705, 0.44], b: [0.705, 0.52], s: 0.02, t: p.emitter });
    } else {
      // Fan coils at the ceiling on circuit C2.
      list.push({ a: [0.2, 0.3], b: [0.3, 0.36], s: 0.04, t: p.emitter });
      list.push({ a: [0.5, 0.3], b: [0.6, 0.36], s: 0.04, t: p.emitter });
    }
    return list;
  }

  function computeBase(m) {
    const p = MODES[m];
    const src = sources(m);
    const field = new Float32Array(cols * rows);
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        const cx = ((x + 0.5) / cols) * W, cy = ((y + 0.5) / rows) * H;
        const u = (cx - box.x) / box.w, v = (cy - box.y) / box.h;
        let t;
        const inHouse = (u > HOUSE.u0 && u < HOUSE.u1 && v > HOUSE.v0 && v < HOUSE.v1) || (v <= HOUSE.v0 && underRoof(u, v));
        if (v >= HOUSE.v1) {
          t = p.soil + (p.outside - p.soil) * Math.max(0, 1 - (v - HOUSE.v1) * 8) * 0.5;
        } else if (inHouse) {
          // Warm air rises.
          t = p.interior + (m === "heat" ? 1.6 : 2.5) * (1 - (v - HOUSE.v0) / (HOUSE.v1 - HOUSE.v0));
          if (v <= HOUSE.v0) t = (t + p.roof) / 2;
        } else {
          t = p.outside + (m === "heat" ? -1.5 : 1.5) * (1 - Math.min(1, Math.max(0, v)));
        }
        for (const s of src) {
          const d2 = segDist2(u, v, s.a, s.b);
          const k = Math.exp(-d2 / (2 * s.s * s.s));
          if (k > 0.002) t += (s.t - t) * k;
        }
        field[y * cols + x] = t;
      }
    }
    blur(field, 2);
    blur(field, 1);
    return field;
  }

  function blur(f, r) {
    const tmp = new Float32Array(f.length);
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        let s = 0, n = 0;
        for (let k = -r; k <= r; k++) {
          const xx = x + k;
          if (xx >= 0 && xx < cols) { s += f[y * cols + xx]; n++; }
        }
        tmp[y * cols + x] = s / n;
      }
    }
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        let s = 0, n = 0;
        for (let k = -r; k <= r; k++) {
          const yy = y + k;
          if (yy >= 0 && yy < rows) { s += tmp[yy * cols + x]; n++; }
        }
        f[y * cols + x] = s / n;
      }
    }
  }

  function layout() {
    const rect = root.getBoundingClientRect();
    W = Math.max(1, rect.width);
    H = Math.max(1, rect.height);
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(W * dpr);
    canvas.height = Math.round(H * dpr);

    const wide = W / H > 1.05;
    TOUR = wide ? TOUR_WIDE : TOUR_NARROW;
    tourIndex = tourIndex % TOUR.length;
    const aspect = 1.3; // scene width / height
    if (wide) {
      const copy = root.querySelector(".tx-hero__copy .tx-lede");
      const rootLeft = root.getBoundingClientRect().left;
      const clear = copy ? copy.getBoundingClientRect().right - rootLeft + 24 : W * 0.45;
      const avail = W - Math.max(clear, W * 0.42) - 104; // leave room for the scale bar
      const h = Math.min(H * 0.78, avail / aspect);
      const w = h * aspect;
      box = { x: W - 104 - w, y: H - h - H * 0.07, w, h };
    } else {
      // Narrow screens: the house leads, the copy follows below it.
      const w = W * 0.94;
      const h = w / 1.7;
      box = { x: (W - w) / 2, y: 64, w, h };
    }

    cols = Math.round(Math.min(240, Math.max(120, W / 6)));
    rows = Math.round(cols * (H / W));
    off = document.createElement("canvas");
    off.width = cols;
    off.height = rows;
    offCtx = off.getContext("2d");
    img = offCtx.createImageData(cols, rows);
    frame = new Float32Array(cols * rows);
    baseHeat = computeBase("heat");
    baseCool = computeBase("cool");
  }

  function sceneToPx(u, v) {
    return [box.x + u * box.w, box.y + v * box.h];
  }

  function sample(xCss, yCss) {
    const x = Math.min(cols - 1, Math.max(0, Math.floor((xCss / W) * cols)));
    const y = Math.min(rows - 1, Math.max(0, Math.floor((yCss / H) * rows)));
    return frame[y * cols + x];
  }

  function zoneAt(xCss, yCss) {
    const u = (xCss - box.x) / box.w, v = (yCss - box.y) / box.h;
    return ZONES.find((z) => z.hit(u, v));
  }

  function easeOutExpo(t) {
    return t >= 1 ? 1 : 1 - Math.pow(2, -10 * t);
  }

  function render(now) {
    if (mixStart) {
      const t = Math.min(1, (now - mixStart) / 1100);
      mix = mixFrom + (mixTo - mixFrom) * easeOutExpo(t);
      if (t >= 1) mixStart = 0;
    }
    T_MIN = SPAN.heat[0] + (SPAN.cool[0] - SPAN.heat[0]) * mix;
    T_MAX = SPAN.heat[1] + (SPAN.cool[1] - SPAN.heat[1]) * mix;
    if (scaleEnds.length === 2) {
      scaleEnds[0].textContent = String(Math.round(T_MAX));
      scaleEnds[1].textContent = String(Math.round(T_MIN));
    }
    const pHeat = MODES.heat.pulse, pCool = MODES.cool.pulse;
    const pulseAmp = pHeat + (pCool - pHeat) * mix;

    // Hot (or cold) water travelling from the outdoor unit through the floor loop.
    const phase = reduced ? 0.35 : ((now / 4200) % 1);
    const path = [PIPE[2], PIPE[1], [0.72, 0.822], [0.1, 0.822]];
    const pulsePt = along(path, phase);
    const [pxp, pyp] = sceneToPx(pulsePt[0], pulsePt[1]);
    const pcx = (pxp / W) * cols, pcy = (pyp / H) * rows;
    const pr = (0.045 * box.w / W) * cols;

    const n = cols * rows;
    for (let i = 0; i < n; i++) frame[i] = baseHeat[i] + (baseCool[i] - baseHeat[i]) * mix;
    const r2 = pr * pr * 2;
    const x0 = Math.max(0, Math.floor(pcx - pr * 3)), x1 = Math.min(cols - 1, Math.ceil(pcx + pr * 3));
    const y0 = Math.max(0, Math.floor(pcy - pr * 3)), y1 = Math.min(rows - 1, Math.ceil(pcy + pr * 3));
    for (let y = y0; y <= y1; y++) {
      for (let x = x0; x <= x1; x++) {
        const dx = x - pcx, dy = y - pcy;
        frame[y * cols + x] += pulseAmp * Math.exp(-(dx * dx + dy * dy) / r2);
      }
    }

    const data = img.data;
    const span = T_MAX - T_MIN;
    for (let i = 0, j = 0; i < n; i++, j += 4) {
      let k = ((frame[i] - T_MIN) / span) * 255;
      k = k < 0 ? 0 : k > 255 ? 255 : k | 0;
      data[j] = LUT[k * 3];
      data[j + 1] = LUT[k * 3 + 1];
      data[j + 2] = LUT[k * 3 + 2];
      data[j + 3] = 255;
    }
    offCtx.putImageData(img, 0, 0);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(off, 0, 0, W, H);
    drawOutline();
    updateSpot(now);
  }

  function along(path, t) {
    const lens = [];
    let total = 0;
    for (let i = 1; i < path.length; i++) {
      const l = Math.hypot(path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1]);
      lens.push(l);
      total += l;
    }
    let d = t * total;
    for (let i = 0; i < lens.length; i++) {
      if (d <= lens[i]) {
        const f = d / lens[i];
        return [path[i][0] + (path[i + 1][0] - path[i][0]) * f, path[i][1] + (path[i + 1][1] - path[i][1]) * f];
      }
      d -= lens[i];
    }
    return path[path.length - 1];
  }

  function drawOutline() {
    ctx.save();
    ctx.lineWidth = 1;
    ctx.strokeStyle = "rgba(255, 248, 230, 0.34)";
    ctx.beginPath();
    const P = (u, v) => sceneToPx(u, v);
    let [x, y] = P(ROOF.left[0], ROOF.left[1]);
    ctx.moveTo(x, y);
    [x, y] = P(ROOF.peak[0], ROOF.peak[1]); ctx.lineTo(x, y);
    [x, y] = P(ROOF.right[0], ROOF.right[1]); ctx.lineTo(x, y);
    const rect = (r) => {
      const [a, b] = P(r.u0, r.v0), [c, d] = P(r.u1, r.v1);
      ctx.rect(a, b, c - a, d - b);
    };
    rect({ u0: HOUSE.u0, v0: HOUSE.v0, u1: HOUSE.u1, v1: HOUSE.v1 });
    [x, y] = P(HOUSE.u0, HOUSE.slab); ctx.moveTo(x, y);
    [x, y] = P(HOUSE.u1, HOUSE.slab); ctx.lineTo(x, y);
    rect(TANK);
    rect(ODU);
    ctx.stroke();

    // Ground line, full width.
    ctx.strokeStyle = "rgba(255, 248, 230, 0.18)";
    ctx.beginPath();
    [x, y] = P(0, HOUSE.v1);
    ctx.moveTo(0, y);
    ctx.lineTo(W, y);
    ctx.stroke();

    // Outdoor unit fan.
    const [fx, fy] = P((ODU.u0 + ODU.u1) / 2, (ODU.v0 + ODU.v1) / 2);
    ctx.strokeStyle = "rgba(255, 248, 230, 0.3)";
    ctx.beginPath();
    ctx.arc(fx, fy, Math.min(box.w * 0.045, box.h * 0.06), 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
  }

  function updateSpot(now) {
    let pos;
    if (spot && now - lastPointer < 5000) {
      pos = spot;
    } else {
      // Guided tour between the zones while nobody is pointing.
      const dwell = 2800;
      if (!tourStart) tourStart = now;
      if (now - tourStart > dwell && !reduced) {
        tourFrom = currentPos || null;
        tourIndex = (tourIndex + 1) % TOUR.length;
        tourStart = now;
      }
      const z = ZONES.find((q) => q.id === TOUR[tourIndex]);
      const target = sceneToPx(z.poi[0], z.poi[1]);
      const t = tourFrom ? easeOutExpo(Math.min(1, (now - tourStart) / 900)) : 1;
      pos = tourFrom
        ? { x: tourFrom.x + (target[0] - tourFrom.x) * t, y: tourFrom.y + (target[1] - tourFrom.y) * t }
        : { x: target[0], y: target[1] };
    }
    currentPos = pos;
    const temp = sample(pos.x, pos.y);
    const z = zoneAt(pos.x, pos.y);

    meter.style.transform = `translate3d(${pos.x}px, ${pos.y}px, 0)`;
    const cardW = card.offsetWidth + 40;
    const wide = W / H > 1.05;
    const right = wide ? W - 96 : W; // keep clear of the scale bar
    const copy = root.querySelector(".tx-hero__copy .tx-lede");
    const copyRight = copy ? copy.getBoundingClientRect().right - root.getBoundingClientRect().left : 0;
    const left = wide && pos.x + cardW > right && pos.x - cardW > copyRight;
    meter.classList.toggle("is-left", left);
    const floor = wide ? H : box.y + box.h; // on phones the copy starts under the house
    meter.classList.toggle("is-up", wide && pos.y + card.offsetHeight + 30 > floor);
    // On narrow screens neither side fits: slide the card back inside the frame.
    if (wide) {
      const overflow = left ? 0 : Math.min(0, right - 12 - (pos.x + cardW - 12));
      card.style.translate = `${overflow}px 0`;
    } else {
      // Phones: the readout docks in the strip between the house and the headline.
      card.style.translate = `${16 - 28 - pos.x}px ${box.y + box.h + 12 - 18 - pos.y}px`;
    }
    meter.classList.toggle("is-ghost", !z.entity);
    out.temp.textContent = `${temp.toFixed(1)} °C`;
    if (out.zone.textContent !== z.label) out.zone.textContent = z.label;
    const ent = z.entity || "not exposed as an entity";
    if (out.entity.textContent !== ent) out.entity.textContent = ent;
    const st = z.state(mode);
    if (out.state.textContent !== st) out.state.textContent = st;

    const f = Math.min(1, Math.max(0, (temp - T_MIN) / (T_MAX - T_MIN)));
    scaleMark.style.setProperty("--at", `${(1 - f) * 100}%`);
    scaleValue.textContent = temp.toFixed(1);
  }

  let currentPos = null;

  function loop(now) {
    raf = 0;
    if (!visible) return;
    render(now);
    if (!reduced || mixStart) raf = requestAnimationFrame(loop);
  }

  function kick() {
    if (!raf && visible) raf = requestAnimationFrame(loop);
  }

  function setMode(next) {
    if (next === mode) return;
    mode = next;
    root.dataset.hvac = next;
    mixFrom = mix;
    mixTo = next === "cool" ? 1 : 0;
    mixStart = performance.now();
    modeButtons.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.mode === next)));
    kick();
  }

  modeButtons.forEach((b) => b.addEventListener("click", () => setMode(b.dataset.mode)));

  const stage = root;
  const onPoint = (e) => {
    const rect = root.getBoundingClientRect();
    const x = e.clientX - rect.left, y = e.clientY - rect.top;
    // Only the scene takes readings; the copy column stays readable.
    if (x < box.x - 24 || y < box.y - 24 || y > box.y + box.h + 24) return;
    spot = { x, y };
    lastPointer = performance.now();
    tourFrom = null;
    kick();
  };
  stage.addEventListener("pointermove", onPoint);
  stage.addEventListener("pointerdown", onPoint);
  stage.addEventListener("pointerleave", () => {
    lastPointer = performance.now() - 4000;
    tourFrom = currentPos;
    tourStart = performance.now();
  });

  let resizeTimer = 0;
  new ResizeObserver(() => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      layout();
      tourFrom = null;
      kick();
      if (reduced) render(performance.now());
    }, 120);
  }).observe(root);

  new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
    kick();
  }).observe(root);

  layout();
  root.dataset.hvac = mode;
  root.classList.add("is-live");
  render(performance.now());
  kick();
})();
