# Credit Risk Dashboard
### P&L Attribution · Hedge Efficiency · Basis Monitor

A Plotly/Dash analytics tool for daily credit portfolio risk oversight — built around the P&L decomposition, hedge efficiency, and bond-CDS basis monitoring workflow used in investment-grade and high-yield credit books.

**Market context:** Built in response to the deteriorating risk profile of lower-rated software and private-credit-adjacent leveraged loan borrowers facing AI-driven business-model disruption (Reuters, Feb 2026) and record private-credit default rates of 9.2% in 2025 (Fitch, April 2026). The sample portfolio reflects this thesis.

---

## Single-Screen Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  Header: Book / Date dropdowns · Export PDF                      │
├────────────┬───────────┬───────────┬──────────────┬─────────────┤
│ Actual P&L │ Explained │ Residual  │ Hedge Eff. % │ Net CS01    │
├────────────────────────┬─────────────────────────────────────────┤
│ Actual vs Explained    │ Hedged vs Unhedged cumulative P&L       │
├────────────────────────┼─────────────────────────────────────────┤
│ Bond–CDS Basis         │ Sector Hedge Ratio                      │
├──────────────────────────────────────────────────────────────────┤
│ Open Exceptions / Alerts                                         │
└──────────────────────────────────────────────────────────────────┘
```

---

## P&L Decomposition

Every dollar of daily P&L is attributed to one of six components:

| Component | Driver |
|---|---|
| **Carry** | Coupon accrual (bonds) / premium paid (CDS) |
| **Spread** | CS01 × daily spread change |
| **Roll** | Roll-down along the credit curve |
| **Basis** | Bond–CDS basis drift (cash vs synthetic) |
| **Event** | Rating migration, credit event, restructuring |
| **Residual** | Unexplained — the primary risk signal |

**Residual > 15%** triggers a warning. **Residual > 25%** triggers a breach. A persistently large residual indicates model mis-specification, data issues, or a regime shift the model does not capture.

---

## Hedge Efficiency

```
Efficiency = 1 - Var(Net P&L, 21d) / Var(Gross P&L, 21d)
```

The sample data embeds a known structural problem: as lower-rated software spreads widen faster than CDX HY implies, the hedge beta drifts above 1.0, the index hedge under-delivers, and efficiency decays. This is visible in the hedged vs unhedged chart and the net CS01 time series.

---

## Bond–CDS Basis

Basis = bond spread − CDS spread. A negative basis means cash bonds trade cheaper than the CDS. For software and private-credit names, the basis drifts materially negative through the sample period — consistent with a liquidity-driven cheapening in cash markets that a CDS-based index hedge cannot capture.

**Thresholds:**
- Warning: basis < −50bps
- Breach: basis < −100bps

---

## Daily PDF Export (4 Sections)

| Section | Content |
|---|---|
| **A — Headline** | Actual P&L, Explained %, Residual %, Hedge Efficiency %, Net CS01, Top 3 movers |
| **B — Driver Breakdown** | Carry / Spread / Roll / Basis / Event / Residual |
| **C — Hedge Review** | Hedge ratio, net CS01, effective beta, bond-CDS basis by issuer |
| **D — Exceptions** | Threshold breaches, stale data, escalation status |

---

## Project Structure

```
credit_risk_dashboard/
├── app/
│   ├── main.py              # Entry point
│   ├── layout.py            # Single-screen layout
│   ├── callbacks.py         # All interactivity + PDF export
│   ├── styles.py            # Centralised design tokens
│   └── components/
│       ├── kpi_cards.py     # Top-row KPI tiles
│       ├── pnl_charts.py    # Actual vs Explained, waterfall
│       ├── basis_charts.py  # Basis time series, sector hedge ratio
│       ├── hedge_tables.py  # Hedge summary table
│       └── alerts_panel.py  # Exceptions / threshold breaches
├── analytics/
│   ├── pnl_decomposition.py # Daily book P&L, top movers, waterfall
│   ├── hedge_efficiency.py  # Rolling efficiency, net CS01
│   └── basis_analysis.py    # Sector basis, alerts
├── data/
│   ├── loaders.py           # CSV loaders (→ SQL in Phase 3)
│   └── sample_data/
│       └── generate_sample.py  # Generates 143-day synthetic dataset
├── config/
│   ├── settings.py
│   └── thresholds.yaml      # All alert thresholds in one place
└── requirements.txt
```

---

## Quickstart

```bash
# 1. Clone and install
git clone https://github.com/DAVIDACHUN/credit_risk_dashboard
cd credit_risk_dashboard
pip install -r requirements.txt

# 2. Generate sample data
python3 data/sample_data/generate_sample.py

# 3. Run dashboard
python3 app/main.py
# → open http://127.0.0.1:8050
```

---

## Roadmap

| Phase | Status | Features |
|---|---|---|
| 1 | ✅ Complete | Sample data · P&L decomposition · Hedge efficiency · Basis analysis |
| 2 | ✅ Complete | Dash app · KPI tiles · All charts · Alerts · PDF export |
| 3 | Planned | SQL integration · Scheduled daily refresh · Comments / escalation workflow |

---

## Sample Portfolio

15-name HY credit book skewed toward the stress thesis:

- **Software / SaaS** (35%) — B/B- rated, persistent spread widening, negative basis
- **Private Credit Adjacent** (36%) — highest spread levels, fastest widening, two downgrade events in the data
- **Healthcare / Retail / Industrials / Energy** — diversifiers with varying dynamics

The two embedded downgrade events (DataSys Corp B-→CCC+ Jan 2026, ShopNet LLC B-→CCC+ Feb 2026) produce visible spikes in the event P&L component and drive residual enlargement in the weeks that follow.

---

*Author: David Achungo — [github.com/DAVIDACHUN](https://github.com/DAVIDACHUN)*
