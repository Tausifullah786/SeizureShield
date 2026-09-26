/* Canvas charts for the explainability visualizations. */

function setupCanvas(id, cssWidth, cssHeight) {
  const canvas = document.getElementById(id);
  const dpr = window.devicePixelRatio || 1;
  canvas.style.width = cssWidth + "px";
  canvas.style.height = cssHeight + "px";
  canvas.width = cssWidth * dpr;
  canvas.height = cssHeight * dpr;
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);
  ctx.font = "12px -apple-system, Segoe UI, sans-serif";
  return ctx;
}

/** Light grey -> dark navy, matching the app palette. */
function heatColor(v) {
  const stops = [
    [241, 245, 249],   // #f1f5f9
    [148, 163, 184],   // #94a3b8
    [15, 27, 38],      // #0f1b26
  ];
  const t = Math.max(0, Math.min(1, v)) * (stops.length - 1);
  const i = Math.min(Math.floor(t), stops.length - 2);
  const f = t - i;
  const c = stops[i].map((s, k) => Math.round(s + (stops[i + 1][k] - s) * f));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}

/* ---------- 1. Horizontal bars, sorted, top channels highlighted ---------- */
function drawChannelBars(id, channelImportance, topChannels) {
  const rows = [...channelImportance].sort((a, b) => b.importance - a.importance);
  const labelW = 90, rightPad = 60, rowH = 22, top = 10;
  const width = 760, height = top + rows.length * rowH + 10;
  const ctx = setupCanvas(id, width, height);
  const barMax = width - labelW - rightPad;

  rows.forEach((row, i) => {
    const y = top + i * rowH;
    const isTop = topChannels.includes(row.channel);

    ctx.fillStyle = isTop ? "#0f1b26" : "#64748b";
    ctx.textAlign = "right";
    ctx.font = isTop ? "600 12px -apple-system, sans-serif" : "12px -apple-system, sans-serif";
    ctx.fillText(row.channel, labelW - 10, y + 14);

    const w = Math.max(2, row.importance * barMax);
    ctx.fillStyle = isTop ? "#c2410c" : "#cbd5e1";
    ctx.fillRect(labelW, y + 4, w, 14);

    ctx.fillStyle = "#64748b";
    ctx.textAlign = "left";
    ctx.font = "12px -apple-system, sans-serif";
    ctx.fillText(row.importance.toFixed(3), labelW + w + 8, y + 14);
  });
}

/* ---------- 2. Time importance line with shaded regions ---------- */
function drawTimeChart(id, timeImportance, regions) {
  const width = 760, height = 240;
  const left = 40, right = 12, top = 12, bottom = 30;
  const ctx = setupCanvas(id, width, height);

  const plotW = width - left - right;
  const plotH = height - top - bottom;
  const n = timeImportance.length;
  const xAt = i => left + (i / (n - 1)) * plotW;
  const yAt = v => top + plotH - v * plotH;

  // shaded important regions
  regions.forEach(r => {
    ctx.fillStyle = "rgba(194,65,12,0.12)";
    ctx.fillRect(xAt(r.start), top, xAt(r.end) - xAt(r.start), plotH);
  });

  // gridlines
  ctx.strokeStyle = "#e2e8f0";
  ctx.lineWidth = 1;
  [0, 0.5, 1].forEach(v => {
    ctx.beginPath();
    ctx.moveTo(left, yAt(v)); ctx.lineTo(width - right, yAt(v)); ctx.stroke();
    ctx.fillStyle = "#64748b"; ctx.textAlign = "right";
    ctx.fillText(v.toFixed(1), left - 8, yAt(v) + 4);
  });

  // filled area
  ctx.beginPath();
  ctx.moveTo(xAt(0), yAt(0));
  timeImportance.forEach((v, i) => ctx.lineTo(xAt(i), yAt(v)));
  ctx.lineTo(xAt(n - 1), yAt(0));
  ctx.closePath();
  ctx.fillStyle = "rgba(15,27,38,0.08)";
  ctx.fill();

  // line
  ctx.beginPath();
  timeImportance.forEach((v, i) => i ? ctx.lineTo(xAt(i), yAt(v)) : ctx.moveTo(xAt(i), yAt(v)));
  ctx.strokeStyle = "#0f1b26";
  ctx.lineWidth = 1.5;
  ctx.stroke();

  // x axis in seconds (256 steps = 4 s)
  ctx.fillStyle = "#64748b";
  ctx.textAlign = "center";
  [0, 1, 2, 3, 4].forEach(sec => {
    const i = Math.min(n - 1, Math.round((sec / 4) * (n - 1)));
    ctx.fillText(sec + "s", xAt(i), height - 10);
  });
}

/* ---------- 3. Heatmap: channels across, time down ---------- */
function drawHeatmap(id, heatmap, channels) {
  const rows = heatmap.length;          // 64 time bins
  const cols = channels.length;         // 23 channels
  const labelH = 74, leftAxis = 40, cellW = 28, cellH = 6;
  const width = leftAxis + cols * cellW + 10;
  const height = labelH + rows * cellH + 24;
  const ctx = setupCanvas(id, width, height);

  // rotated channel labels along the top
  ctx.save();
  ctx.fillStyle = "#64748b";
  channels.forEach((name, c) => {
    ctx.save();
    ctx.translate(leftAxis + c * cellW + cellW / 2 + 4, labelH - 8);
    ctx.rotate(-Math.PI / 3);
    ctx.textAlign = "left";
    ctx.fillText(name, 0, 0);
    ctx.restore();
  });
  ctx.restore();

  // cells
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      ctx.fillStyle = heatColor(heatmap[r][c]);
      ctx.fillRect(leftAxis + c * cellW, labelH + r * cellH, cellW - 1, cellH - 0.5);
    }
  }

  // time axis on the left (64 bins = 4 s)
  ctx.fillStyle = "#64748b";
  ctx.textAlign = "right";
  [0, 1, 2, 3, 4].forEach(sec => {
    const r = Math.min(rows, Math.round((sec / 4) * rows));
    ctx.fillText(sec + "s", leftAxis - 8, labelH + r * cellH + 4);
  });
}