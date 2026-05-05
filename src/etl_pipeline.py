
from pathlib import Path
import pandas as pd
import numpy as np

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def read_csv(name):
    return pd.read_csv(RAW_DIR / name)

def standardize_columns(df):
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def validate_scada(scada):
    scada = standardize_columns(scada)
    scada["event_start"] = pd.to_datetime(scada["event_start"], errors="coerce")
    scada["event_end"] = pd.to_datetime(scada["event_end"], errors="coerce")
    scada["duration_min"] = pd.to_numeric(scada["duration_min"], errors="coerce")

    conditions = [
        scada["event_start"].isna(),
        scada["duration_min"].isna(),
        scada["duration_min"] <= 0,
        scada["duration_min"] > 1440,
        scada["event_end"].isna(),
    ]
    labels = [
        "missing_start_time",
        "missing_duration",
        "negative_or_zero_duration",
        "duration_above_24h",
        "missing_end_time",
    ]
    scada["validation_flag"] = "valid"
    for cond, label in zip(conditions, labels):
        scada.loc[cond, "validation_flag"] = label

    scada["month"] = scada["event_start"].dt.to_period("M").astype(str)
    return scada

def validate_oms(oms):
    oms = standardize_columns(oms)
    oms["outage_date"] = pd.to_datetime(oms["outage_date"], errors="coerce")
    oms["customers_interrupted"] = pd.to_numeric(oms["customers_interrupted"], errors="coerce")
    oms["reported_duration_min"] = pd.to_numeric(oms["reported_duration_min"], errors="coerce")
    oms["validation_flag"] = "valid"

    oms.loc[oms["outage_date"].isna(), "validation_flag"] = "missing_outage_date"
    oms.loc[oms["customers_interrupted"].isna() | (oms["customers_interrupted"] < 0), "validation_flag"] = "invalid_customer_count"
    oms.loc[oms["reported_duration_min"].isna() | (oms["reported_duration_min"] <= 0), "validation_flag"] = "invalid_duration"
    oms.loc[oms["reported_duration_min"] > 1440, "validation_flag"] = "duration_above_24h"
    oms["month"] = oms["outage_date"].dt.to_period("M").astype(str)
    return oms

def build_monthly_outage_fact(scada, oms, feeders):
    valid_oms = oms[oms["validation_flag"] == "valid"].copy()
    feeders_small = feeders[["feeder_id", "company", "region_type", "connected_customers"]].copy()

    fact = valid_oms.merge(feeders_small, on=["feeder_id", "company"], how="left")
    fact["customer_minutes_interrupted"] = fact["customers_interrupted"] * fact["reported_duration_min"]

    monthly = fact.groupby(["month", "company", "region_type"], as_index=False).agg(
        outage_events=("oms_report_id", "count"),
        interrupted_customers=("customers_interrupted", "sum"),
        customer_minutes_interrupted=("customer_minutes_interrupted", "sum"),
        planned_events=("planned_flag", "sum"),
        complaints_count=("complaints_count", "sum")
    )
    customer_base = feeders_small.groupby(["company", "region_type"], as_index=False).agg(
        total_customers=("connected_customers", "sum"),
        feeder_count=("feeder_id", "count")
    )
    monthly = monthly.merge(customer_base, on=["company", "region_type"], how="left")
    return monthly

def build_monthly_commercial_fact(energy, billing, meter, feeders):
    for df in [energy, billing, meter, feeders]:
        df.columns = [c.strip().lower() for c in df.columns]

    energy_billing = energy.merge(billing, on=["month", "company", "feeder_id"], how="left")
    all_data = energy_billing.merge(meter, on=["month", "company", "feeder_id"], how="left")
    all_data = all_data.merge(feeders[["feeder_id", "company", "region_type", "connected_customers"]], on=["feeder_id", "company"], how="left")

    monthly = all_data.groupby(["month", "company", "region_type"], as_index=False).agg(
        energy_injected_mwh=("energy_injected_mwh", "sum"),
        energy_billed_mwh=("energy_billed_mwh", "sum"),
        estimated_technical_loss_mwh=("estimated_technical_loss_mwh", "sum"),
        revenue_billed_egp_m=("revenue_billed_egp_m", "sum"),
        revenue_collected_egp_m=("revenue_collected_egp_m", "sum"),
        expected_meter_reads=("expected_meter_reads", "sum"),
        actual_meter_reads=("actual_meter_reads", "sum"),
        estimated_reads=("estimated_reads", "sum"),
        manual_corrections=("manual_corrections", "sum"),
        billing_records_count=("billing_records_count", "sum"),
        billing_error_count=("billing_error_count", "sum"),
        total_customers=("connected_customers", "sum")
    )
    return monthly

def calculate_kpis(outage_fact, commercial_fact, scada_validated, oms_validated):
    kpi = outage_fact.merge(
        commercial_fact,
        on=["month", "company", "region_type", "total_customers"],
        how="outer"
    )

    kpi["saidi_hours_per_customer"] = kpi["customer_minutes_interrupted"] / kpi["total_customers"] / 60
    kpi["saifi_interruptions_per_customer"] = kpi["interrupted_customers"] / kpi["total_customers"]
    kpi["caidi_minutes_per_interruption"] = np.where(
        kpi["saifi_interruptions_per_customer"] > 0,
        kpi["saidi_hours_per_customer"] / kpi["saifi_interruptions_per_customer"] * 60,
        np.nan
    )

    kpi["total_loss_pct"] = (kpi["energy_injected_mwh"] - kpi["energy_billed_mwh"]) / kpi["energy_injected_mwh"] * 100
    kpi["technical_loss_pct"] = kpi["estimated_technical_loss_mwh"] / kpi["energy_injected_mwh"] * 100
    kpi["non_technical_loss_pct"] = kpi["total_loss_pct"] - kpi["technical_loss_pct"]
    kpi["collection_efficiency_pct"] = kpi["revenue_collected_egp_m"] / kpi["revenue_billed_egp_m"] * 100
    kpi["meter_read_completeness_pct"] = kpi["actual_meter_reads"] / kpi["expected_meter_reads"] * 100
    kpi["billing_error_rate_pct"] = kpi["billing_error_count"] / kpi["billing_records_count"] * 100

    scada_quality = scada_validated.groupby(["month", "company"], as_index=False).agg(
        scada_records=("scada_event_id", "count"),
        valid_scada_records=("validation_flag", lambda s: (s == "valid").sum())
    )
    scada_quality["scada_validity_pct"] = scada_quality["valid_scada_records"] / scada_quality["scada_records"] * 100

    oms_quality = oms_validated.groupby(["month", "company"], as_index=False).agg(
        oms_records=("oms_report_id", "count"),
        valid_oms_records=("validation_flag", lambda s: (s == "valid").sum())
    )
    oms_quality["oms_validity_pct"] = oms_quality["valid_oms_records"] / oms_quality["oms_records"] * 100

    kpi = kpi.merge(scada_quality[["month", "company", "scada_validity_pct"]], on=["month", "company"], how="left")
    kpi = kpi.merge(oms_quality[["month", "company", "oms_validity_pct"]], on=["month", "company"], how="left")

    kpi["data_quality_score_pct"] = (
        kpi["scada_validity_pct"].fillna(0) * 0.30 +
        kpi["oms_validity_pct"].fillna(0) * 0.30 +
        kpi["meter_read_completeness_pct"].fillna(0) * 0.25 +
        (100 - kpi["billing_error_rate_pct"].fillna(100)).clip(lower=0) * 0.15
    )

    kpi["management_flag"] = "OK"
    kpi.loc[kpi["total_loss_pct"] > 18, "management_flag"] = "High losses"
    kpi.loc[kpi["saidi_hours_per_customer"] > 1.2, "management_flag"] = "Reliability concern"
    kpi.loc[kpi["data_quality_score_pct"] < 92, "management_flag"] = "Data quality risk"

    return kpi.sort_values(["company", "month"])

def build_benchmark(kpi):
    benchmark = kpi.groupby(["company", "region_type"], as_index=False).agg(
        saidi_ytd=("saidi_hours_per_customer", "sum"),
        saifi_avg=("saifi_interruptions_per_customer", "mean"),
        caidi_avg=("caidi_minutes_per_interruption", "mean"),
        total_loss_pct_avg=("total_loss_pct", "mean"),
        non_technical_loss_pct_avg=("non_technical_loss_pct", "mean"),
        collection_efficiency_pct_avg=("collection_efficiency_pct", "mean"),
        meter_read_completeness_pct_avg=("meter_read_completeness_pct", "mean"),
        data_quality_score_pct_avg=("data_quality_score_pct", "mean"),
    )

    # Composite score: lower SAIDI/losses are better, higher collection/data quality are better.
    for col in ["saidi_ytd", "total_loss_pct_avg", "non_technical_loss_pct_avg"]:
        benchmark[f"{col}_rank"] = benchmark[col].rank(ascending=True)
    for col in ["collection_efficiency_pct_avg", "data_quality_score_pct_avg"]:
        benchmark[f"{col}_rank"] = benchmark[col].rank(ascending=False)

    rank_cols = [c for c in benchmark.columns if c.endswith("_rank")]
    benchmark["benchmark_score"] = benchmark[rank_cols].mean(axis=1)
    benchmark["overall_rank"] = benchmark["benchmark_score"].rank(ascending=True).astype(int)
    return benchmark.sort_values("overall_rank")

def main():
    feeders = standardize_columns(read_csv("asset_feeder_master.csv"))
    scada = validate_scada(read_csv("scada_events_raw.csv"))
    oms = validate_oms(read_csv("oms_outage_reports_raw.csv"))
    energy = standardize_columns(read_csv("monthly_energy_balance_raw.csv"))
    billing = standardize_columns(read_csv("billing_collection_raw.csv"))
    meter = standardize_columns(read_csv("meter_reading_quality_raw.csv"))

    outage_fact = build_monthly_outage_fact(scada, oms, feeders)
    commercial_fact = build_monthly_commercial_fact(energy, billing, meter, feeders)
    kpi = calculate_kpis(outage_fact, commercial_fact, scada, oms)
    benchmark = build_benchmark(kpi)

    scada.to_csv(PROCESSED_DIR / "scada_events_validated.csv", index=False)
    oms.to_csv(PROCESSED_DIR / "oms_reports_validated.csv", index=False)
    outage_fact.to_csv(PROCESSED_DIR / "fact_monthly_outages.csv", index=False)
    commercial_fact.to_csv(PROCESSED_DIR / "fact_monthly_commercial.csv", index=False)
    kpi.to_csv(PROCESSED_DIR / "kpi_monthly_company.csv", index=False)
    benchmark.to_csv(PROCESSED_DIR / "benchmark_distribution_companies.csv", index=False)

    print("ETL complete. Processed files written to data/processed/")
    print({
        "kpi_rows": len(kpi),
        "benchmark_rows": len(benchmark),
        "processed_dir": str(PROCESSED_DIR)
    })

if __name__ == "__main__":
    main()
