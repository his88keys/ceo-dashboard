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

// ---- Rendering (browser only) ----

var PILLAR_ORDER = ["Marketing", "Sales", "Operations", "Finance"];

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
        '<span class="dot"></span>' +
        '<span class="target">Target ' + targetStr + '</span>' +
        '<span class="trend trend-' + trend.dir + '">' + TREND_GLYPH[trend.dir] + ' ' + trendPctStr + '</span>' +
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

function renderPillars(data) {
  return PILLAR_ORDER.map(function (pillar) {
    var metrics = data.metrics.filter(function (m) { return m.pillar === pillar; });
    if (metrics.length === 0) return "";
    var cards = metrics.map(cardHTML).join("");
    return (
      '<section class="pillar">' +
        '<h2 class="pillar-title">' + pillar + '</h2>' +
        '<div class="grid">' + cards + '</div>' +
      '</section>'
    );
  }).join("");
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
  root.innerHTML = renderHeadline(data) + renderPillars(data);
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
    sparklinePath: sparklinePath
  };
}
