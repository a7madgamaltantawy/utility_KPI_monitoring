
from pathlib import Path
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)
np.random.seed(42)

COMPANIES = [
    "North Cairo", "South Cairo", "Alexandria", "Canal", "North Delta",
    "South Delta", "Middle Egypt", "Upper Egypt", "Beheira"
]

REGION_TYPE = {
    "North Cairo": "Urban",
    "South Cairo": "Urban",
    "Alexandria": "Urban",
    "Canal": "Mixed",
    "North Delta": "Mixed",
    "South Delta": "Mixed",
    "Middle Egypt": "Rural",
    "Upper Egypt": "Rural",
    "Beheira": "Mixed",
}

CUSTOMER_BASE = {
    "North Cairo": 1450000,
    "South Cairo": 1320000,
    "Alexandria": 1180000,
    "Canal": 900000,
    "North Delta": 1600000,
    "South Delta": 1520000,
    "Middle Egypt": 1100000,
    "Upper Egypt": 1350000,
    "Beheira": 1280000,
}

CAUSES = [
    "Feeder fault", "Transformer fault", "Planned maintenance", "Overload",
    "Weather", "Third-party damage", "Protection trip", "Unknown"
]

def make_feeders():
    rows = []
    feeder_id = 1
    for company in COMPANIES:
        n = {"Urban": 35, "Mixed": 45, "Rural": 55}[REGION_TYPE[company]]
        for i in range(n):
            customers = random.randint(4000, 28000)
            length_km = round(random.uniform(3, 25) if REGION_TYPE[company] == "Urban" else random.uniform(12, 85), 2)
            rows.append({
                "feeder_id": f"FDR-{feeder_id:04d}",
                "company": company,
                "region_type": REGION_TYPE[company],
                "voltage_level": "MV",
                "feeder_name": f"{company[:3].upper()}_{i+1:03d}",
                "connected_customers": customers,
                "line_length_km": length_km,
                "transformer_count": random.randint(8, 95),
                "technical_loss_factor": round(random.uniform(0.045, 0.105), 4)
            })
            feeder_id += 1
    return pd.DataFrame(rows)

def make_customer_master(feeders):
    rows = []
    customer_id = 1
    for _, f in feeders.iterrows():
        # sample customers, not full population
        sample_n = min(260, max(80, int(f.connected_customers / 100)))
        for _ in range(sample_n):
            rows.append({
                "customer_id": f"CUST-{customer_id:07d}",
                "feeder_id": f.feeder_id,
                "company": f.company,
                "customer_type": random.choices(
                    ["Residential", "Commercial", "Industrial", "Public"],
                    weights=[78, 15, 4, 3]
                )[0],
                "meter_type": random.choices(["Smart", "AMR", "Manual"], weights=[20, 35, 45])[0],
                "active": random.choices([1, 0], weights=[98, 2])[0]
            })
            customer_id += 1
    return pd.DataFrame(rows)

def random_timestamp(month_start):
    day = random.randint(0, 27)
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    return month_start + timedelta(days=day, hours=hour, minutes=minute)

def make_scada_events(feeders):
    rows = []
    event_id = 1
    months = pd.date_range("2025-01-01", "2025-12-01", freq="MS")
    for month_start in months:
        for _, f in feeders.iterrows():
            base_events = {"Urban": 1.5, "Mixed": 2.4, "Rural": 3.2}[f.region_type]
            n_events = np.random.poisson(base_events)
            for _ in range(n_events):
                start = random_timestamp(month_start.to_pydatetime())
                duration = int(np.random.gamma(shape=2.0, scale={"Urban": 25, "Mixed": 35, "Rural": 50}[f.region_type]))
                duration = max(5, min(duration, 720))
                end = start + timedelta(minutes=duration)

                # inject some messy records
                if random.random() < 0.015:
                    duration = -duration
                if random.random() < 0.015:
                    end = None

                rows.append({
                    "scada_event_id": f"SCADA-{event_id:08d}",
                    "source_system": "SCADA",
                    "company": f.company,
                    "feeder_id": f.feeder_id,
                    "event_start": start.strftime("%Y-%m-%d %H:%M:%S"),
                    "event_end": "" if end is None else end.strftime("%Y-%m-%d %H:%M:%S"),
                    "duration_min": duration,
                    "cause": random.choice(CAUSES),
                    "breaker_status": random.choice(["OPEN", "CLOSED", "UNKNOWN"]),
                    "voltage_before_kv": round(random.uniform(10.8, 11.4), 2),
                    "voltage_after_kv": round(random.uniform(0, 10.8), 2)
                })
                event_id += 1
    return pd.DataFrame(rows)

def make_oms_reports(scada_events, feeders):
    rows = []
    report_id = 1
    sampled = scada_events.sample(frac=0.72, random_state=7)
    for _, e in sampled.iterrows():
        f = feeders.loc[feeders.feeder_id == e.feeder_id].iloc[0]
        affected = random.randint(50, int(max(100, f.connected_customers * random.uniform(0.04, 0.65))))
        rows.append({
            "oms_report_id": f"OMS-{report_id:08d}",
            "linked_scada_event_id": e.scada_event_id if random.random() > 0.08 else "",
            "source_system": random.choice(["OMS", "Call Center", "Manual Report"]),
            "company": e.company,
            "feeder_id": e.feeder_id,
            "outage_date": str(e.event_start)[:10],
            "customers_interrupted": affected,
            "reported_duration_min": e.duration_min + random.randint(-10, 30),
            "planned_flag": 1 if e.cause == "Planned maintenance" else 0,
            "complaints_count": int(affected * random.uniform(0.005, 0.04))
        })
        report_id += 1

    # add orphan reports not linked to SCADA
    for _ in range(1200):
        f = feeders.sample(1, random_state=random.randint(0, 999999)).iloc[0]
        date = datetime(2025, random.randint(1, 12), random.randint(1, 28))
        affected = random.randint(20, int(max(50, f.connected_customers * random.uniform(0.02, 0.25))))
        rows.append({
            "oms_report_id": f"OMS-{report_id:08d}",
            "linked_scada_event_id": "",
            "source_system": random.choice(["OMS", "Call Center", "Manual Report"]),
            "company": f.company,
            "feeder_id": f.feeder_id,
            "outage_date": date.strftime("%Y-%m-%d"),
            "customers_interrupted": affected,
            "reported_duration_min": random.randint(10, 240),
            "planned_flag": random.choice([0, 0, 0, 1]),
            "complaints_count": int(affected * random.uniform(0.005, 0.04))
        })
        report_id += 1
    return pd.DataFrame(rows)

def make_monthly_energy(feeders):
    rows = []
    months = pd.date_range("2025-01-01", "2025-12-01", freq="MS")
    for month_start in months:
        for _, f in feeders.iterrows():
            season = 1.18 if month_start.month in [7, 8, 9] else 1.0
            billed_mwh = f.connected_customers * random.uniform(0.16, 0.32) * season
            loss_base = {"Urban": 0.105, "Mixed": 0.135, "Rural": 0.17}[f.region_type]
            non_tech = random.uniform(0.01, 0.07)
            total_loss = min(0.33, loss_base + non_tech + random.uniform(-0.015, 0.015))
            injected_mwh = billed_mwh / (1 - total_loss)
            rows.append({
                "month": month_start.strftime("%Y-%m"),
                "company": f.company,
                "feeder_id": f.feeder_id,
                "energy_injected_mwh": round(injected_mwh, 2),
                "energy_billed_mwh": round(billed_mwh, 2),
                "estimated_technical_loss_mwh": round(injected_mwh * f.technical_loss_factor, 2)
            })
    return pd.DataFrame(rows)

def make_billing_collection(energy):
    rows = []
    for _, e in energy.iterrows():
        tariff_egp_kwh = random.uniform(0.75, 1.25)
        billed_egp_m = e.energy_billed_mwh * 1000 * tariff_egp_kwh / 1_000_000
        company = e.company
        collection_rate = {
            "North Cairo": 0.96, "South Cairo": 0.94, "Alexandria": 0.95,
            "Canal": 0.91, "North Delta": 0.90, "South Delta": 0.89,
            "Middle Egypt": 0.84, "Upper Egypt": 0.82, "Beheira": 0.88
        }[company] + random.uniform(-0.035, 0.025)
        rows.append({
            "month": e.month,
            "company": company,
            "feeder_id": e.feeder_id,
            "revenue_billed_egp_m": round(billed_egp_m, 3),
            "revenue_collected_egp_m": round(billed_egp_m * max(0.65, min(0.99, collection_rate)), 3),
            "billing_records_count": random.randint(3500, 26000),
            "billing_error_count": random.randint(0, 180)
        })
    return pd.DataFrame(rows)

def make_meter_reads(feeders):
    rows = []
    months = pd.date_range("2025-01-01", "2025-12-01", freq="MS")
    meter_id = 1
    for month_start in months:
        for _, f in feeders.iterrows():
            expected = f.connected_customers
            completeness = {
                "Urban": random.uniform(0.93, 0.995),
                "Mixed": random.uniform(0.88, 0.985),
                "Rural": random.uniform(0.78, 0.96),
            }[f.region_type]
            read_count = int(expected * completeness)
            estimated_count = int(expected * random.uniform(0.01, 0.12))
            rows.append({
                "month": month_start.strftime("%Y-%m"),
                "company": f.company,
                "feeder_id": f.feeder_id,
                "expected_meter_reads": int(expected),
                "actual_meter_reads": int(read_count),
                "estimated_reads": int(estimated_count),
                "manual_corrections": random.randint(0, 320)
            })
            meter_id += 1
    return pd.DataFrame(rows)

def main():
    feeders = make_feeders()
    customers = make_customer_master(feeders)
    scada = make_scada_events(feeders)
    oms = make_oms_reports(scada, feeders)
    energy = make_monthly_energy(feeders)
    billing = make_billing_collection(energy)
    meter = make_meter_reads(feeders)

    feeders.to_csv(RAW_DIR / "asset_feeder_master.csv", index=False)
    customers.to_csv(RAW_DIR / "customer_master_sample.csv", index=False)
    scada.to_csv(RAW_DIR / "scada_events_raw.csv", index=False)
    oms.to_csv(RAW_DIR / "oms_outage_reports_raw.csv", index=False)
    energy.to_csv(RAW_DIR / "monthly_energy_balance_raw.csv", index=False)
    billing.to_csv(RAW_DIR / "billing_collection_raw.csv", index=False)
    meter.to_csv(RAW_DIR / "meter_reading_quality_raw.csv", index=False)

    print("Synthetic raw data generated in data/raw/")
    print({
        "feeders": len(feeders),
        "customers_sample": len(customers),
        "scada_events": len(scada),
        "oms_reports": len(oms),
        "energy_rows": len(energy),
        "billing_rows": len(billing),
        "meter_rows": len(meter),
    })

if __name__ == "__main__":
    main()
