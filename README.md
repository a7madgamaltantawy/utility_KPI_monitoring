# ⚡ Utility KPI Monitoring App

A Python-based application for electricity distribution company KPI monitoring.

This project simulates a real consulting workflow:
raw data → ETL → validation → SQLite database → KPI mart → API → dashboard.

---

##  Business Objective

Monitor and benchmark distribution company performance using:

- SAIDI (reliability)
- SAIFI (frequency)
- CAIDI
- Total losses (technical + non-technical)
- Collection efficiency
- Meter-read completeness
- Data quality score
- Benchmark ranking

---

##  Architecture

    Raw Data (SCADA / OMS / Billing / Metering)
            ↓
    ETL Pipeline (Python)
            ↓
    Validation Layer
            ↓
    SQLite Database (Data Mart)
            ↓
    FastAPI Backend
            ↓
    Streamlit Dashboard

---

##  Data Sources (Simulated)

- SCADA events
- OMS outage reports
- Billing & collection data
- Meter reading quality
- Energy balance data
- Feeder asset master
- Customer data

---

##  Project Structure

    utility_kpi_monitoring_app/
    ├── backend/
    ├── dashboard/
    ├── data/
    ├── docs/
    ├── sql/
    ├── src/
    ├── requirements.txt
    └── README.md

---

##  Setup

Create virtual environment:

    python -m venv .venv

Activate it:

    # macOS / Linux
    source .venv/bin/activate

    # Windows PowerShell
    .venv\Scripts\Activate.ps1

Install dependencies:

    pip install -r requirements.txt

---

##  Run the Project

1. Generate raw data

    python src/generate_synthetic_data.py

2. Run ETL pipeline

    python src/etl_pipeline.py

3. Create SQLite database

    python src/create_sqlite_database.py

4. Run FastAPI backend

    python -m uvicorn backend.main:app --reload

Open API docs:

    http://127.0.0.1:8000/docs

5. Run Streamlit dashboard

    streamlit run dashboard/app.py

---

##  KPI Formulas

SAIDI

    SAIDI = Customer Minutes Interrupted / Total Customers / 60

SAIFI

    SAIFI = Interrupted Customers / Total Customers

CAIDI

    CAIDI = SAIDI / SAIFI × 60

Total Loss %

    Total Loss % = (Energy Injected - Energy Billed) / Energy Injected × 100

Non-Technical Loss %

    Non-Technical Loss % = Total Loss % - Technical Loss %

Collection Efficiency %

    Collection Efficiency % = Revenue Collected / Revenue Billed × 100

---

##  Database Design

Main Layers

- Dimensions: dim_company, dim_feeder
- Raw tables: SCADA, OMS, billing, metering
- Validated tables: cleaned outage data
- Fact tables:
  - fact_monthly_outages
  - fact_monthly_commercial
- KPI Mart: kpi_monthly_company
- Benchmark table: benchmark_distribution_companies

SQL Views

- vw_company_monthly_kpis
- vw_company_benchmark
- vw_data_quality_summary

---

##  Dashboard Features

- Executive KPI overview
- SAIDI / SAIFI trends
- Losses & collection analysis
- Data quality monitoring
- Benchmark comparison across companies

---

##  Interview Explanation

I built a full KPI monitoring pipeline for distribution utilities.
The system ingests multi-source data (SCADA, OMS, billing), validates it, calculates KPIs such as SAIDI and losses, stores them in a structured SQLite data mart, exposes them via FastAPI, and visualizes them in a Streamlit dashboard for benchmarking and decision support.

---

##  Limitations

- Synthetic data (not real utility data)
- Simplified technical loss estimation
- No real SCADA / MDMS integration
- No real-time streaming
- No authentication / security layer
- SQLite used instead of production database

---

## Future Improvements

- Replace SQLite with PostgreSQL / cloud warehouse
- Add feeder-level drill-down
- Add geospatial visualization
- Add anomaly detection for non-technical losses
- Add Power BI dashboard
- Integrate real APIs (SCADA / billing / MDMS)
