# Commodity Cost Intelligence & Volatility Radar

An end-to-end market intelligence pipeline and interactive executive dashboard built to monitor commodity price dynamics, track rolling volatility, and automatically flag statistical shock anomalies.

![Dashboard Preview](dashboard_preview.png)

---

## 1. Project Overview & Business Value

In volatile macroeconomic environments, commodity procurement and corporate finance teams need rapid, data-backed insights to manage cost risks. This project delivers an automated workflow that transforms raw financial market feeds into an executive-ready business intelligence report.

* **Trend Benchmarking:** Evaluates spot price movements against medium-term trend baselines (SMA 90D).
* **Automated Shock Detection:** Flags statistical price shocks using Z-Score modeling on logarithmic returns ($\vert{}Z\vert{} \ge 2.5$) to provide early warnings.
* **Multi-Asset Monitoring:** Enables cross-commodity comparison across energy and agricultural assets (Crude Oil, Natural Gas, Corn, Soybean, Wheat).

---

## 2. Technical Stack & Pipeline Architecture

### Python Data Engineering (`pipeline_commodities.py`)
* **Libraries:** `yfinance`, `pandas`, `numpy`
* **Data Ingestion:** Automated daily historical price extraction starting from 2023.
* **Feature Engineering:**
  * **Log Returns:** Daily compounded return modeling.
  * **Annualized Rolling Volatility:** 30-day window scaled to annual trading days ($\sigma \times \sqrt{252}$).
  * **Trend Moving Averages:** Simple Moving Average over 30-day and 90-day horizons (`SMA_30`, `SMA_90`).
  * **Z-Score Anomaly Engine:** Identifies extreme tail events where $\vert{}Z\vert{} \ge 2.5$, categorizing shocks into `Price Spike` or `Sharp Drop`.

### Power BI Executive Report (`commodity_report.pbix`)
* Clean data modeling with explicit US locale formatting for financial decimal precision.
* Dynamic measures built with DAX for average pricing and annualized volatility aggregation.

---

## 3. How to Read the Dashboard

1. **Asset Slicer (Left Panel):** Filter the entire report by individual commodity or view aggregated market exposure.
2. **Executive KPI Cards (Top Right):**
   * **Shock Alerts:** Total count of statistical outlier days detected for the selected asset.
   * **Avg Volatility:** The average annualized volatility regime over the monitored window.
   * **Current / Avg Price:** Benchmark reference spot price.
3. **Price Dynamics vs. 90-Day Trend (Center Line Chart):**
   * **Continuous Line:** Spot market closing price.
   * **Dashed / Trend Line:** 90-day moving average, showing support/resistance baseline levels.
4. **Shock Radar Audit Table (Right Panel):**
   * Granular audit trail displaying strictly the high-impact anomaly dates, shock classifications (`Price Spike` vs `Sharp Drop`), spot levels, and associated Z-Score magnitudes.

---

## 4. How to Run Locally

```bash
# 1. Install dependencies
pip install pandas numpy yfinance

# 2. Run data pipeline to refresh dataset
python pipeline_commodities.py

# 3. Open Dashboard
# Open 'commodity_report.pbix' in Power BI Desktop and click 'Refresh'.