// CEO Dashboard — pure helpers + render logic. No build, no deps.

var AMBER_BAND = 0.10; // within 10% of target on the wrong side = amber
var FLAT_EPS = 0.5;    // percent change under this magnitude = flat

function formatValue(value, unit, opts) {
  opts = opts || {};
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  var n = Number(value);
  switch (unit) {
    case "currency": {
      var s = Math.round(n).toLocaleString("en-US");
      return "$" + s;
    }
    case "percent":
      return n.toFixed(1) + "%";
    case "days":
      return Math.round(n).toLocaleString("en-US") + "d";
    case "months":
      return (Math.round(n * 10) / 10) + " mo";
    case "ratio":
      return n.toFixed(1) + ":1";
    case "number":
    default:
      return Math.round(n).toLocaleString("en-US");
  }
}

function statusFor(latest, target, direction) {
  if (latest === null || latest === undefined || Number.isNaN(latest)) return "gray";
  if (target === null || target === undefined || Number.isNaN(target)) return "gray";
  var l = Number(latest), t = Number(target);
  if (direction === "down") {
    if (l <= t) return "green";
    if (l <= t * (1 + AMBER_BAND)) return "amber";
    return "red";
  }
  // default "up"
  if (l >= t) return "green";
  if (l >= t * (1 - AMBER_BAND)) return "amber";
  return "red";
}

function trendFor(values) {
  if (!Array.isArray(values) || values.length < 2) return { dir: "flat", pct: 0 };
  var prev = Number(values[values.length - 2]);
  var last = Number(values[values.length - 1]);
  if (!prev) return { dir: last > 0 ? "up" : "flat", pct: 0 };
  var pct = ((last - prev) / Math.abs(prev)) * 100;
  var rounded = Math.round(pct * 10) / 10;
  var dir = Math.abs(rounded) < FLAT_EPS ? "flat" : (rounded > 0 ? "up" : "down");
  return { dir: dir, pct: dir === "flat" ? 0 : rounded };
}

// Is a trend movement GOOD for this metric, given its direction?
// Returns "good" | "bad" | "flat". Lower-is-better metrics (direction "down")
// invert: a downward trend is good, an upward trend is bad.
function trendPolarity(trendDir, direction) {
  if (trendDir === "flat") return "flat";
  var wantsDown = direction === "down";
  var isDown = trendDir === "down";
  return (isDown === wantsDown) ? "good" : "bad";
}

function sparklinePath(values, width, height) {
  if (!Array.isArray(values) || values.length < 2) return "";
  var nums = values.map(Number);
  var min = Math.min.apply(null, nums);
  var max = Math.max.apply(null, nums);
  var span = max - min;
  var n = nums.length;
  var pad = 2; // keep line off the top/bottom edges
  var parts = [];
  for (var i = 0; i < n; i++) {
    var x = Math.round((i / (n - 1)) * width);
    var norm = span === 0 ? 0.5 : (nums[i] - min) / span; // flat -> middle
    // SVG y grows downward; higher value = higher on chart = smaller y
    var y = Math.round(pad + (1 - norm) * (height - 2 * pad));
    parts.push((i === 0 ? "M" : "L") + x + " " + y);
  }
  return parts.join(" ");
}

// Deterministic, order-independent hash of the data's numbers. Used to detect
// whether baked AI insights are stale (data changed since they were generated).
// FNV-1a 32-bit -> 8-char hex. No deps, stable across Node and browsers.
function dataSignature(data) {
  var metrics = (data && data.metrics) || [];
  var parts = metrics.map(function (m) {
    return [m.id, m.direction, m.target, (m.values || []).join(",")].join("|");
  }).sort();
  var basis = ((data && data.company) || "") + "::" + parts.join(";");
  var h = 0x811c9dc5;
  for (var i = 0; i < basis.length; i++) {
    h ^= basis.charCodeAt(i);
    h = (h + ((h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24))) >>> 0;
  }
  return ("0000000" + h.toString(16)).slice(-8);
}

// Count how many metrics are off-track (red) vs at-risk (amber) right now.
function summarize(metrics) {
  var red = 0, amber = 0;
  (metrics || []).forEach(function (m) {
    var v = (m.values && m.values.length) ? m.values[m.values.length - 1] : null;
    var s = statusFor(v, m.target, m.direction);
    if (s === "red") red++;
    else if (s === "amber") amber++;
  });
  return { red: red, amber: amber };
}

// ---- Rendering (browser only) ----

var PILLAR_ORDER = ["Marketing", "Sales", "Operations", "Finance"];

// Escape untrusted text (AI-generated insight strings) before inserting as HTML.
function escapeHTML(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function metricById(data, id) {
  for (var i = 0; i < data.metrics.length; i++) {
    if (data.metrics[i].id === id) return data.metrics[i];
  }
  return null;
}

function latestOf(metric) {
  var v = metric && metric.values;
  if (!Array.isArray(v) || v.length === 0) return null;
  return v[v.length - 1];
}

var TREND_GLYPH = { up: "▲", down: "▼", flat: "–" }; // triangle up / down / en dash

function cardHTML(metric) {
  var latest = latestOf(metric);
  var status = statusFor(latest, metric.target, metric.direction);
  var trend = trendFor(metric.values || []);
  var polarity = trendPolarity(trend.dir, metric.direction); // good | bad | flat
  var hasData = latest !== null && latest !== undefined;
  var spark = sparklinePath(metric.values || [], 120, 32);
  var valueStr = hasData ? formatValue(latest, metric.unit) : "no data";
  var targetStr = formatValue(metric.target, metric.unit);
  var trendPctStr = trend.dir === "flat" ? "" : (Math.abs(trend.pct) + "%");
  return (
    '<div class="card status-' + status + '">' +
      '<div class="card-top">' +
        '<span class="card-label">' + metric.label + '</span>' +
        '<span class="tag tag-' + metric.type + '">' + metric.type + '</span>' +
      '</div>' +
      '<div class="card-value">' + valueStr + '</div>' +
      '<div class="card-meta">' +
        '<span class="target">Target ' + targetStr + '</span>' +
        '<span class="trend trend-' + polarity + '" title="' + trendPctStr + ' vs last period">' + TREND_GLYPH[trend.dir] + ' ' + trendPctStr + '</span>' +
      '</div>' +
      (spark ? '<svg class="spark" viewBox="0 0 120 32" preserveAspectRatio="none"><path d="' + spark + '"/></svg>' : '') +
    '</div>'
  );
}

function renderHeadline(data) {
  var ids = data.headline || [];
  var cards = ids.map(function (id) {
    var m = metricById(data, id);
    return m ? cardHTML(m) : "";
  }).join("");
  return '<section class="headline"><div class="grid grid-headline">' + cards + '</div></section>';
}

function renderPillars(data, insights) {
  var pillarText = (insights && insights.pillars) || {};
  return PILLAR_ORDER.map(function (pillar) {
    var metrics = data.metrics.filter(function (m) { return m.pillar === pillar; });
    if (metrics.length === 0) return "";
    var cards = metrics.map(cardHTML).join("");
    var note = pillarText[pillar]
      ? '<p class="pillar-insight">' + escapeHTML(pillarText[pillar]) + '</p>'
      : "";
    return (
      '<section class="pillar">' +
        '<h2 class="pillar-title">' + pillar + '</h2>' +
        '<div class="grid">' + cards + '</div>' +
        note +
      '</section>'
    );
  }).join("");
}

function renderSummary(data, insights) {
  if (!insights || !insights.summary) return "";
  var stale = insights.signature && insights.signature !== dataSignature(data);
  var staleNote = stale
    ? '<span class="summary-stale">Numbers changed since these insights — regenerate (node tools/generate-insights.mjs).</span>'
    : "";
  return (
    '<section class="summary-card">' +
      '<div class="summary-eyebrow">AI summary' + staleNote + '</div>' +
      '<p class="summary-body">' + escapeHTML(insights.summary) + '</p>' +
    '</section>'
  );
}

function initToggle() {
  var btn = document.getElementById("theme-toggle");
  if (!btn) return;
  var saved = null;
  try { saved = window.localStorage.getItem("ceo-theme"); } catch (e) {}
  if (saved === "dark") document.body.classList.add("dark");
  btn.addEventListener("click", function () {
    document.body.classList.toggle("dark");
    var mode = document.body.classList.contains("dark") ? "dark" : "light";
    try { window.localStorage.setItem("ceo-theme", mode); } catch (e) {}
  });
}

function init() {
  var root = document.getElementById("app");
  if (!root) return;
  var data = window.DASHBOARD_DATA;
  if (!data || !Array.isArray(data.metrics)) {
    root.innerHTML = '<div class="empty">No data found. Edit <code>data.js</code> to add your numbers.</div>';
    return;
  }
  var header = document.getElementById("company-name");
  if (header) header.textContent = data.company || "CEO Dashboard";
  var periodEl = document.getElementById("period");
  if (periodEl && data.period && data.period.labels && data.period.labels.length) {
    var labels = data.period.labels;
    periodEl.textContent = labels[0] + " – " + labels[labels.length - 1];
  }
  var chip = document.getElementById("status-summary");
  if (chip) {
    var s = summarize(data.metrics);
    if (s.red || s.amber) {
      chip.textContent = s.red + " off-track · " + s.amber + " at risk";
      chip.className = "status-chip " + (s.red ? "chip-red" : "chip-amber");
    } else {
      chip.textContent = "All on track";
      chip.className = "status-chip chip-green";
    }
  }
  var insights = window.DASHBOARD_INSIGHTS;
  root.innerHTML = renderSummary(data, insights) + renderHeadline(data) + renderPillars(data, insights);
  initToggle();
}

if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", init);
}

// Dual export: Node test can require this; browser ignores module.
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    formatValue: formatValue,
    statusFor: statusFor,
    trendFor: trendFor,
    trendPolarity: trendPolarity,
    summarize: summarize,
    dataSignature: dataSignature,
    sparklinePath: sparklinePath
  };
}
