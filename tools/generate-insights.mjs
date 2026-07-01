#!/usr/bin/env node
/**
 * Generate AI insights for the CEO Dashboard and bake them into a static
 * insights.js. Run from the repo root (the folder that holds data.js):
 *
 *   node tools/generate-insights.mjs           # writes insights.js
 *   node tools/generate-insights.mjs --dry-run # print JSON, don't write
 *
 * Requires OPENAI_API_KEY in the environment (or in a .env file in this folder
 * or its parent). Model via INSIGHTS_MODEL (default gpt-4o). Zero dependencies.
 */
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const DATA_PATH = path.join(ROOT, "data.js");
const APP_PATH = path.join(ROOT, "app.js");
const OUT_PATH = path.join(ROOT, "insights.js");

const DRY = process.argv.includes("--dry-run");

// --- tiny .env loader (OPENAI_API_KEY=... lines; ignores comments) ----------
function loadEnv() {
  for (const p of [path.join(ROOT, ".env"), path.join(ROOT, "..", ".env")]) {
    if (!fs.existsSync(p)) continue;
    for (const line of fs.readFileSync(p, "utf8").split(/\r?\n/)) {
      const m = /^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/.exec(line);
      if (m && !process.env[m[1]]) {
        process.env[m[1]] = m[2].replace(/^["']|["']$/g, "");
      }
    }
  }
}

// --- load window.DASHBOARD_DATA from data.js in a vm sandbox ----------------
function loadData() {
  const src = fs.readFileSync(DATA_PATH, "utf8");
  const ctx = { window: {} };
  vm.createContext(ctx);
  vm.runInContext(src, ctx, { filename: "data.js" });
  const data = ctx.window.DASHBOARD_DATA;
  if (!data || !Array.isArray(data.metrics)) {
    throw new Error("data.js did not set window.DASHBOARD_DATA.metrics");
  }
  return data;
}

async function loadHelpers() {
  // app.js dual-exports its pure helpers via module.exports (CJS).
  const mod = await import(pathToFileURL(APP_PATH).href);
  return mod.default || mod;
}

// --- build a compact, grounded description of the numbers -------------------
function describe(data, h) {
  const labels = (data.period && data.period.labels) || [];
  const lines = data.metrics.map((m) => {
    const vals = m.values || [];
    const latest = vals.length ? vals[vals.length - 1] : null;
    const status = h.statusFor(latest, m.target, m.direction);
    const trend = h.trendFor(vals);
    const polarity = h.trendPolarity(trend.dir, m.direction);
    const val = h.formatValue(latest, m.unit);
    const tgt = h.formatValue(m.target, m.unit);
    const better = m.direction === "down" ? "lower is better" : "higher is better";
    const move = trend.dir === "flat" ? "flat" : `${trend.dir} ${Math.abs(trend.pct)}% (${polarity})`;
    return `- [${m.pillar}] ${m.label} (${m.type}, ${better}): ${val}, target ${tgt}, status ${status}, trend ${move}`;
  });
  return `Company: ${data.company}\nPeriod: ${labels[0]} to ${labels[labels.length - 1]}\nMetrics:\n${lines.join("\n")}`;
}

const SYSTEM = `You are a sharp CFO/operator writing plain-language board commentary on a
one-page CEO dashboard. Rules:
- Use ONLY the numbers provided. Invent nothing. Reference real metric names and values.
- Respect direction: for "lower is better" metrics (churn, CAC, sales cycle, A/R days) a
  DECREASE is good and an increase is bad.
- No hype, no filler, no buzzwords. Short, concrete, useful.
Return STRICT JSON only:
{"summary":"<2-3 sentences: overall health, biggest win, biggest risk>",
 "pillars":{"Marketing":"<1-2 sentences: what the row shows + weakest metric + one action>",
            "Sales":"<...>","Operations":"<...>","Finance":"<...>"}}`;

async function callOpenAI(desc) {
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error("ERROR: OPENAI_API_KEY not set (env or .env). Cannot generate insights.");
    process.exit(1);
  }
  const model = process.env.INSIGHTS_MODEL || "gpt-4o";
  const body = {
    model,
    response_format: { type: "json_object" },
    messages: [
      { role: "system", content: SYSTEM },
      { role: "user", content: `Write the dashboard commentary for this data:\n\n${desc}` },
    ],
  };
  if (!model.startsWith("gpt-5") && !model.startsWith("o")) body.temperature = 0.3;

  const resp = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${key}` },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    console.error(`ERROR: OpenAI ${resp.status}: ${await resp.text()}`);
    process.exit(1);
  }
  const json = await resp.json();
  const txt = json.choices[0].message.content.trim();
  return { parsed: JSON.parse(txt), model };
}

async function main() {
  loadEnv();
  const data = loadData();
  const h = await loadHelpers();
  const desc = describe(data, h);
  const { parsed, model } = await callOpenAI(desc);

  const out = {
    generatedAt: process.env.INSIGHTS_GENERATED_AT || new Date().toISOString(),
    model,
    signature: h.dataSignature(data),
    summary: parsed.summary || "",
    pillars: parsed.pillars || {},
  };

  if (DRY) {
    console.log(JSON.stringify(out, null, 2));
    return;
  }
  const file =
    "// Auto-generated by tools/generate-insights.mjs. Do not edit by hand.\n" +
    "// Rerun after editing data.js: node tools/generate-insights.mjs\n" +
    "window.DASHBOARD_INSIGHTS = " + JSON.stringify(out, null, 2) + ";\n";
  fs.writeFileSync(OUT_PATH, file);
  console.log(`Wrote ${path.relative(ROOT, OUT_PATH)} (model ${model}, signature ${out.signature}).`);
}

main().catch((e) => { console.error(e); process.exit(1); });
