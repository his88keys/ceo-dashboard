const assert = require("assert");
const h = require("../app.js");

// formatValue
assert.strictEqual(h.formatValue(120000, "currency"), "$120,000");
assert.strictEqual(h.formatValue(1234.5, "currency"), "$1,235"); // 0 decimals, rounded
assert.strictEqual(h.formatValue(12.34, "percent"), "12.3%");
assert.strictEqual(h.formatValue(42, "number"), "42");
assert.strictEqual(h.formatValue(1500, "number"), "1,500");
assert.strictEqual(h.formatValue(7, "days"), "7d");
assert.strictEqual(h.formatValue(3.2, "ratio"), "3.2:1");
assert.strictEqual(h.formatValue(500, "wat"), "500"); // unknown unit -> plain number
assert.strictEqual(h.formatValue(null, "currency"), "—"); // missing value
console.log("formatValue OK");

// statusFor — direction "up" (higher is better)
assert.strictEqual(h.statusFor(120, 100, "up"), "green"); // at/above target
assert.strictEqual(h.statusFor(100, 100, "up"), "green");
assert.strictEqual(h.statusFor(95, 100, "up"), "amber");  // within 10% below
assert.strictEqual(h.statusFor(80, 100, "up"), "red");    // >10% below
// statusFor — direction "down" (lower is better)
assert.strictEqual(h.statusFor(80, 100, "down"), "green"); // at/below target
assert.strictEqual(h.statusFor(100, 100, "down"), "green");
assert.strictEqual(h.statusFor(108, 100, "down"), "amber"); // within 10% above
assert.strictEqual(h.statusFor(130, 100, "down"), "red");   // >10% above
// missing inputs
assert.strictEqual(h.statusFor(null, 100, "up"), "gray");
assert.strictEqual(h.statusFor(50, null, "up"), "gray");
console.log("statusFor OK");

// trendFor — latest vs previous value
assert.deepStrictEqual(h.trendFor([100, 110]), { dir: "up", pct: 10 });
assert.deepStrictEqual(h.trendFor([100, 90]), { dir: "down", pct: -10 });
assert.deepStrictEqual(h.trendFor([100, 100]), { dir: "flat", pct: 0 });
assert.deepStrictEqual(h.trendFor([100]), { dir: "flat", pct: 0 }); // single point
assert.deepStrictEqual(h.trendFor([]), { dir: "flat", pct: 0 });    // empty
assert.strictEqual(h.trendFor([1000, 1003]).dir, "flat");           // under epsilon
console.log("trendFor OK");

// sparklinePath — SVG path "d" string
assert.strictEqual(h.sparklinePath([5], 100, 30), "");   // <2 points -> empty
assert.strictEqual(h.sparklinePath([], 100, 30), "");
{
  var d = h.sparklinePath([0, 10], 100, 30);
  assert.ok(d.startsWith("M"), "path starts with M");
  assert.strictEqual((d.match(/L/g) || []).length, 1); // 2 points -> one L
  assert.ok(d.indexOf("M0 ") === 0, "first x is 0");
  assert.ok(d.indexOf("L100 ") !== -1, "last x is width");
}
{
  var d2 = h.sparklinePath([5, 5, 5], 100, 30);
  assert.ok(d2.indexOf("NaN") === -1, "no NaN in flat series");
  assert.strictEqual((d2.match(/[ML]/g) || []).length, 3);
}
console.log("sparklinePath OK");
