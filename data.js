// Edit this file to plug in your own numbers. This is the ONLY file most users touch.
// values[] must line up with period.labels (same length, same order).
window.DASHBOARD_DATA = {
  company: "Acme Co",
  period: { labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"] },
  headline: ["revenue", "grossProfit", "cash", "ltvCac"],
  metrics: [
    // Headline vitals (featured in the top row; not repeated in a pillar section)
    { id: "revenue", label: "Revenue", pillar: "Headline", type: "lagging", unit: "currency", target: 120000, direction: "up", values: [90000, 96000, 104000, 110000, 118000, 121000] },
    { id: "grossProfit", label: "Gross Profit", pillar: "Headline", type: "lagging", unit: "currency", target: 72000, direction: "up", values: [52000, 55000, 60000, 63000, 68000, 70000] },
    { id: "cash", label: "Cash Position", pillar: "Headline", type: "lagging", unit: "currency", target: 250000, direction: "up", values: [180000, 195000, 210000, 228000, 245000, 262000] },

    // Finance
    { id: "grossMargin", label: "Gross Margin", pillar: "Finance", type: "lagging", unit: "percent", target: 60, direction: "up", values: [57.8, 57.3, 57.7, 57.3, 57.6, 57.9] },
    { id: "netProfit", label: "Net Profit", pillar: "Finance", type: "lagging", unit: "currency", target: 24000, direction: "up", values: [12000, 14000, 17000, 18500, 21000, 22500] },
    { id: "runway", label: "Cash Runway", pillar: "Finance", type: "lagging", unit: "months", target: 12, direction: "up", values: [8, 8.5, 9, 10, 11, 12] },
    { id: "arDays", label: "A/R Days", pillar: "Finance", type: "lagging", unit: "days", target: 30, direction: "down", values: [52, 48, 45, 41, 38, 35] },

    // Marketing
    { id: "leads", label: "Leads", pillar: "Marketing", type: "leading", unit: "number", target: 800, direction: "up", values: [520, 560, 610, 690, 740, 810] },
    { id: "cpl", label: "Cost per Lead", pillar: "Marketing", type: "lagging", unit: "currency", target: 25, direction: "down", values: [38, 35, 32, 29, 27, 24] },
    { id: "traffic", label: "Traffic", pillar: "Marketing", type: "leading", unit: "number", target: 40000, direction: "up", values: [22000, 25000, 28000, 31000, 35000, 38000] },
    { id: "mqls", label: "MQLs", pillar: "Marketing", type: "leading", unit: "number", target: 300, direction: "up", values: [180, 200, 225, 250, 275, 290] },

    // Sales
    { id: "conversion", label: "Conversion Rate", pillar: "Sales", type: "leading", unit: "percent", target: 25, direction: "up", values: [18, 19.5, 20.2, 21.8, 23.1, 24.0] },
    { id: "dealSize", label: "Avg Deal Size", pillar: "Sales", type: "lagging", unit: "currency", target: 5000, direction: "up", values: [3800, 4000, 4200, 4500, 4700, 4900] },
    { id: "salesCycle", label: "Sales Cycle", pillar: "Sales", type: "lagging", unit: "days", target: 30, direction: "down", values: [48, 45, 42, 38, 35, 33] },
    { id: "newRevenue", label: "New Revenue", pillar: "Sales", type: "lagging", unit: "currency", target: 40000, direction: "up", values: [24000, 27000, 31000, 34000, 37000, 39000] },

    // Operations
    { id: "fulfillment", label: "Fulfillment Time", pillar: "Operations", type: "lagging", unit: "days", target: 3, direction: "down", values: [6, 5.5, 5, 4.5, 4, 3.5] },
    { id: "csat", label: "CSAT", pillar: "Operations", type: "leading", unit: "percent", target: 90, direction: "up", values: [82, 84, 85, 87, 88, 89] },
    { id: "churn", label: "Churn", pillar: "Operations", type: "lagging", unit: "percent", target: 3, direction: "down", values: [6.5, 6.0, 5.4, 4.8, 4.2, 3.6] },
    { id: "capacity", label: "Capacity", pillar: "Operations", type: "leading", unit: "percent", target: 85, direction: "up", values: [70, 72, 75, 78, 80, 83] },

    // Headline-only derived metric
    { id: "ltvCac", label: "LTV:CAC", pillar: "Headline", type: "lagging", unit: "ratio", target: 3, direction: "up", values: [1.8, 2.0, 2.3, 2.6, 2.9, 3.1] }
  ]
};
