from fastapi import FastAPI, HTTPException
from backend.database import query_db

app = FastAPI(
    title="Utility KPI Monitoring API",
    description="API for distribution company KPIs: SAIDI, SAIFI, losses, benchmarking, and data quality.",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "Utility KPI Monitoring API is running"}

@app.get("/companies")
def get_companies():
    df = query_db("""
        SELECT DISTINCT company_name, region_type
        FROM kpi_monthly_company
        ORDER BY company_name
    """)
    return df.to_dict(orient="records")

@app.get("/kpis/{company_name}")
def get_company_kpis(company_name: str):
    df = query_db("""
        SELECT *
        FROM vw_company_monthly_kpis
        WHERE company_name = ?
        ORDER BY month
    """, (company_name,))

    if df.empty:
        raise HTTPException(status_code=404, detail="Company not found")

    return df.to_dict(orient="records")

@app.get("/benchmark")
def get_benchmark():
    df = query_db("""
        SELECT *
        FROM vw_company_benchmark
        ORDER BY overall_rank
    """)
    return df.to_dict(orient="records")

@app.get("/data-quality")
def get_data_quality():
    df = query_db("""
        SELECT *
        FROM vw_data_quality_summary
        ORDER BY avg_data_quality_score_pct ASC
    """)
    return df.to_dict(orient="records")

@app.get("/flags")
def get_management_flags():
    df = query_db("""
        SELECT company_name, month, management_flag,
               saidi_hours_per_customer,
               total_loss_pct,
               data_quality_score_pct
        FROM kpi_monthly_company
        WHERE management_flag != 'OK'
        ORDER BY month, company_name
    """)
    return df.to_dict(orient="records")