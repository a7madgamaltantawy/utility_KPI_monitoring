# Database Schema Explanation — Utility KPI Monitoring App

## 1. Big Picture

The database is designed as a professional KPI data mart for electricity distribution companies.

The flow is:

```text
Dimension Tables
    ↓
Raw Staging Tables
    ↓
Validated Tables
    ↓
Fact Tables
    ↓
KPI Mart
    ↓
Benchmark Tables and Reporting Views
    ↓
Dashboard
```

The main objective is to create a traceable path from raw utility data to final regulatory KPIs such as SAIDI, SAIFI, losses, collection efficiency, and data quality.

---

## 2. Dimension Tables

### dim_company

This table stores the distribution company name and its region type.

Example fields:

```text
company_name
region_type
```

It is the master list of companies.

### dim_feeder

This table stores feeder-level asset data.

Example fields:

```text
feeder_id
company_name
region_type
connected_customers
line_length_km
transformer_count
technical_loss_factor
```

This is very important because many raw operational records are linked to feeders.

Relationship:

```text
dim_company 1 → many dim_feeder
```

Meaning:

One distribution company has many feeders.

---

## 3. Raw Staging Tables

These tables store data as received from source systems before cleaning.

### scada_events_raw

Represents events from SCADA/DMS.

Example:

```text
feeder trip
event_start
event_end
duration_min
breaker_status
cause
```

### oms_outage_reports_raw

Represents OMS, call-center, or manual outage reports.

Example:

```text
customers_interrupted
reported_duration_min
planned_flag
complaints_count
```

### monthly_energy_balance_raw

Stores monthly feeder-level energy balance.

Example:

```text
energy_injected_mwh
energy_billed_mwh
estimated_technical_loss_mwh
```

### billing_collection_raw

Stores billing and collection data.

Example:

```text
revenue_billed_egp_m
revenue_collected_egp_m
billing_error_count
```

### meter_reading_quality_raw

Stores meter reading quality information.

Example:

```text
expected_meter_reads
actual_meter_reads
estimated_reads
manual_corrections
```

Relationship:

```text
dim_feeder 1 → many raw records
```

Meaning:

Each feeder can have many SCADA events, OMS reports, billing records, meter records, and energy records.

---

## 4. Validated Tables

### scada_events_validated

This table is created after applying validation rules to SCADA records.

Validation examples:

```text
missing_start_time
missing_duration
negative_or_zero_duration
duration_above_24h
missing_end_time
valid
```

### oms_reports_validated

This table is created after validating outage reports.

Validation examples:

```text
missing_outage_date
invalid_customer_count
invalid_duration
duration_above_24h
valid
```

Why this matters:

SAIDI and SAIFI depend directly on duration and customers interrupted. If bad outage records are not flagged, the reliability KPIs become misleading.

---

## 5. Fact Tables

Fact tables are aggregated analytical tables.

### fact_monthly_outages

Grain:

```text
one row per company per month
```

Main fields:

```text
outage_events
interrupted_customers
customer_minutes_interrupted
planned_events
complaints_count
total_customers
```

Used for:

```text
SAIDI
SAIFI
CAIDI
```

### fact_monthly_commercial

Grain:

```text
one row per company per month
```

Main fields:

```text
energy_injected_mwh
energy_billed_mwh
estimated_technical_loss_mwh
revenue_billed_egp_m
revenue_collected_egp_m
actual_meter_reads
expected_meter_reads
billing_error_count
```

Used for:

```text
total losses
technical losses
non-technical losses
collection efficiency
meter-read completeness
billing quality
```

---

## 6. KPI Mart

### kpi_monthly_company

This is the core analytical table used by the dashboard.

Grain:

```text
one row per company per month
```

It combines:

```text
fact_monthly_outages
fact_monthly_commercial
SCADA validity
OMS validity
meter quality
billing quality
```

Main KPIs:

```text
SAIDI
SAIFI
CAIDI
total_loss_pct
technical_loss_pct
non_technical_loss_pct
collection_efficiency_pct
meter_read_completeness_pct
data_quality_score_pct
management_flag
```

Key formulas:

```text
SAIDI = Customer Minutes Interrupted / Total Customers / 60

SAIFI = Interrupted Customers / Total Customers

CAIDI = SAIDI / SAIFI × 60

Total Loss % = (Energy Injected - Energy Billed) / Energy Injected × 100

Non-Technical Loss % = Total Loss % - Technical Loss %

Collection Efficiency % = Revenue Collected / Revenue Billed × 100
```

---

## 7. Benchmark Table

### benchmark_distribution_companies

Grain:

```text
one row per company
```

It summarizes company performance over the full period.

Used for:

```text
ranking companies
comparing SAIDI
comparing losses
comparing collection efficiency
comparing data quality
```

This is useful for incentive-based regulation because it allows the regulator to compare distribution companies using standardized KPI definitions.

---

## 8. Reporting Views

Views are simplified SQL layers used by the dashboard.

### vw_company_monthly_kpis

Used for the monthly KPI dashboard.

### vw_company_benchmark

Used for ranking and benchmarking companies.

### vw_data_quality_summary

Used for auditing the quality of the reported data.

Why views are professional:

They hide complex joins and calculations from the dashboard and provide clean reporting-ready datasets.

---

## 9. How to Explain This in an Interview

You can say:

> I designed the database in layers. First, I created dimension tables for companies and feeders. Then I staged raw SCADA, OMS, billing, energy, and meter-reading data. After that, I created validation tables to flag bad outage and commercial records. Then I aggregated the data into monthly outage and commercial fact tables. Finally, I created a KPI mart and SQL reporting views used by the dashboard.

A stronger consulting version:

> The purpose of the schema is traceability. A regulator or consultant can trace every KPI back to the source data, check whether the data passed validation, and compare companies using consistent definitions.

---

## 10. Most Important Relationships

```text
dim_company 1 → many dim_feeder

dim_feeder 1 → many scada_events_raw

dim_feeder 1 → many oms_outage_reports_raw

dim_feeder 1 → many monthly_energy_balance_raw

dim_feeder 1 → many billing_collection_raw

dim_feeder 1 → many meter_reading_quality_raw

scada_events_raw → scada_events_validated

oms_outage_reports_raw → oms_reports_validated

oms_reports_validated → fact_monthly_outages

monthly_energy_balance_raw + billing_collection_raw + meter_reading_quality_raw
    → fact_monthly_commercial

fact_monthly_outages + fact_monthly_commercial
    → kpi_monthly_company

kpi_monthly_company
    → benchmark_distribution_companies

kpi_monthly_company + benchmark_distribution_companies
    → reporting views
    → dashboard
```

---

## 11. Simple Mental Model

Think of the schema like this:

```text
Raw data answers: What happened?

Validation answers: Can we trust it?

Fact tables answer: What happened per month and company?

KPI mart answers: How did the company perform?

Benchmark answers: How does each company compare to others?

Dashboard answers: What should management or regulator act on?
```
