// Alternate sample: early SaaS startup. To use: copy this object into data.js.
window.DASHBOARD_DATA = {
  company: "Nimbus SaaS",
  period: { labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"] },
  headline: ["revenue", "grossProfit", "cash", "ltvCac"],
  metrics: [
    { id: "revenue", label: "MRR", pillar: "Finance", type: "lagging", unit: "currency", target: 50000, direction: "up", values: [22000, 27000, 33000, 39000, 45000, 51000] },
    { id: "grossProfit", label: "Gross Profit", pillar: "Finance", type: "lagging", unit: "currency", target: 40000, direction: "up", values: [17000, 21000, 26000, 31000, 36000, 41000] },
    { id: "grossMargin", label: "Gross Margin", pillar: "Finance", type: "lagging", unit: "percent", target: 80, direction: "up", values: [77, 78, 79, 79.5, 80, 80.4] },
    { id: "netProfit", label: "Net Profit", pillar: "Finance", type: "lagging", unit: "currency", target: 5000, direction: "up", values: [-8000, -4000, -1000, 1500, 3500, 6000] },
    { id: "cash", label: "Cash Position", pillar: "Finance", type: "lagging", unit: "currency", target: 300000, direction: "up", values: [420000, 400000, 385000, 372000, 365000, 360000] },
    { id: "runway", label: "Cash Runway", pillar: "Finance", type: "lagging", unit: "number", target: 18, direction: "up", values: [24, 22, 21, 20, 19, 18] },

    { id: "leads", label: "Signups", pillar: "Marketing", type: "leading", unit: "number", target: 1200, direction: "up", values: [700, 820, 940, 1050, 1150, 1240] },
    { id: "cpl", label: "CAC", pillar: "Marketing", type: "lagging", unit: "currency", target: 120, direction: "down", values: [180, 168, 155, 142, 130, 122] },
    { id: "traffic", label: "Traffic", pillar: "Marketing", type: "leading", unit: "number", target: 60000, direction: "up", values: [30000, 36000, 42000, 48000, 54000, 59000] },
    { id: "mqls", label: "Trials", pillar: "Marketing", type: "leading", unit: "number", target: 400, direction: "up", values: [240, 275, 310, 340, 370, 395] },

    { id: "conversion", label: "Trial→Paid", pillar: "Sales", type: "leading", unit: "percent", target: 20, direction: "up", values: [12, 13.5, 15, 16.8, 18.2, 19.5] },
    { id: "dealSize", label: "ARPU", pillar: "Sales", type: "lagging", unit: "currency", target: 90, direction: "up", values: [62, 66, 71, 77, 83, 88] },
    { id: "salesCycle", label: "Time to Value", pillar: "Sales", type: "lagging", unit: "days", target: 2, direction: "down", values: [7, 6, 5, 4, 3, 2.5] },
    { id: "newRevenue", label: "New MRR", pillar: "Sales", type: "lagging", unit: "currency", target: 8000, direction: "up", values: [4000, 5000, 6000, 6800, 7500, 8200] },

    { id: "fulfillment", label: "Support Response", pillar: "Operations", type: "lagging", unit: "days", target: 1, direction: "down", values: [3, 2.5, 2, 1.6, 1.3, 1.1] },
    { id: "csat", label: "CSAT", pillar: "Operations", type: "leading", unit: "percent", target: 92, direction: "up", values: [85, 86, 88, 89, 90, 91] },
    { id: "churn", label: "Monthly Churn", pillar: "Operations", type: "lagging", unit: "percent", target: 4, direction: "down", values: [9, 8, 7, 6, 5, 4.5] },
    { id: "capacity", label: "Uptime", pillar: "Operations", type: "leading", unit: "percent", target: 99.9, direction: "up", values: [99.2, 99.4, 99.6, 99.7, 99.8, 99.85] },

    { id: "ltvCac", label: "LTV:CAC", pillar: "Headline", type: "lagging", unit: "ratio", target: 3, direction: "up", values: [1.2, 1.5, 1.9, 2.3, 2.7, 3.0] }
  ]
};
