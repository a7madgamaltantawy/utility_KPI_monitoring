
from pathlib import Path
import sqlite3
import pandas as pd

DB_PATH = Path("data/database/utility_kpi.db")
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
SCHEMA_PATH = Path("sql/schema.sql")

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def load_csv(path):
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    # Professional DB naming: use company_name instead of ambiguous "company"
    if "company" in df.columns:
        df = df.rename(columns={"company": "company_name"})
    return df

def write_table(conn, table, df):
    df.to_sql(table, conn, if_exists="append", index=False)

def main():
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError("Missing sql/schema.sql")

    conn = sqlite3.connect(DB_PATH)

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    feeder = load_csv(RAW_DIR / "asset_feeder_master.csv")
    dim_company = feeder[["company_name", "region_type"]].drop_duplicates().sort_values("company_name")
    write_table(conn, "dim_company", dim_company)

    write_table(conn, "dim_feeder", feeder)
    write_table(conn, "customer_master_sample", load_csv(RAW_DIR / "customer_master_sample.csv"))
    write_table(conn, "scada_events_raw", load_csv(RAW_DIR / "scada_events_raw.csv"))
    write_table(conn, "oms_outage_reports_raw", load_csv(RAW_DIR / "oms_outage_reports_raw.csv"))
    write_table(conn, "monthly_energy_balance_raw", load_csv(RAW_DIR / "monthly_energy_balance_raw.csv"))
    write_table(conn, "billing_collection_raw", load_csv(RAW_DIR / "billing_collection_raw.csv"))
    write_table(conn, "meter_reading_quality_raw", load_csv(RAW_DIR / "meter_reading_quality_raw.csv"))

    write_table(conn, "scada_events_validated", load_csv(PROCESSED_DIR / "scada_events_validated.csv"))
    write_table(conn, "oms_reports_validated", load_csv(PROCESSED_DIR / "oms_reports_validated.csv"))
    write_table(conn, "fact_monthly_outages", load_csv(PROCESSED_DIR / "fact_monthly_outages.csv"))
    write_table(conn, "fact_monthly_commercial", load_csv(PROCESSED_DIR / "fact_monthly_commercial.csv"))
    write_table(conn, "kpi_monthly_company", load_csv(PROCESSED_DIR / "kpi_monthly_company.csv"))
    write_table(conn, "benchmark_distribution_companies", load_csv(PROCESSED_DIR / "benchmark_distribution_companies.csv"))

    conn.commit()

    # quick smoke test
    counts = pd.read_sql_query("""
        SELECT 'companies' AS table_name, COUNT(*) AS row_count FROM dim_company
        UNION ALL SELECT 'feeders', COUNT(*) FROM dim_feeder
        UNION ALL SELECT 'scada_raw', COUNT(*) FROM scada_events_raw
        UNION ALL SELECT 'oms_raw', COUNT(*) FROM oms_outage_reports_raw
        UNION ALL SELECT 'monthly_kpis', COUNT(*) FROM kpi_monthly_company
        UNION ALL SELECT 'benchmark', COUNT(*) FROM benchmark_distribution_companies;
    """, conn)

    print(f"SQLite database created: {DB_PATH}")
    print(counts.to_string(index=False))
    conn.close()

if __name__ == "__main__":
    main()
