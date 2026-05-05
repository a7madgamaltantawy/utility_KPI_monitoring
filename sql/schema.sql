
-- SQLite schema for Distribution Company KPI Monitoring
-- This schema separates raw source tables, validated fact tables, KPI marts, and benchmark outputs.

PRAGMA foreign_keys = ON;

DROP VIEW IF EXISTS vw_company_monthly_kpis;
DROP VIEW IF EXISTS vw_company_benchmark;
DROP VIEW IF EXISTS vw_data_quality_summary;

DROP TABLE IF EXISTS benchmark_distribution_companies;
DROP TABLE IF EXISTS kpi_monthly_company;
DROP TABLE IF EXISTS fact_monthly_commercial;
DROP TABLE IF EXISTS fact_monthly_outages;
DROP TABLE IF EXISTS oms_reports_validated;
DROP TABLE IF EXISTS scada_events_validated;
DROP TABLE IF EXISTS meter_reading_quality_raw;
DROP TABLE IF EXISTS billing_collection_raw;
DROP TABLE IF EXISTS monthly_energy_balance_raw;
DROP TABLE IF EXISTS oms_outage_reports_raw;
DROP TABLE IF EXISTS scada_events_raw;
DROP TABLE IF EXISTS customer_master_sample;
DROP TABLE IF EXISTS dim_feeder;
DROP TABLE IF EXISTS dim_company;

CREATE TABLE dim_company (
    company_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL UNIQUE,
    region_type TEXT NOT NULL CHECK(region_type IN ('Urban', 'Mixed', 'Rural'))
);

CREATE TABLE dim_feeder (
    feeder_id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    region_type TEXT NOT NULL,
    voltage_level TEXT NOT NULL,
    feeder_name TEXT,
    connected_customers INTEGER NOT NULL CHECK(connected_customers >= 0),
    line_length_km REAL,
    transformer_count INTEGER,
    technical_loss_factor REAL,
    FOREIGN KEY (company_name) REFERENCES dim_company(company_name)
);

CREATE TABLE customer_master_sample (
    customer_id TEXT PRIMARY KEY,
    feeder_id TEXT NOT NULL,
    company_name TEXT NOT NULL,
    customer_type TEXT,
    meter_type TEXT,
    active INTEGER,
    FOREIGN KEY (feeder_id) REFERENCES dim_feeder(feeder_id)
);

CREATE TABLE scada_events_raw (
    scada_event_id TEXT PRIMARY KEY,
    source_system TEXT,
    company_name TEXT NOT NULL,
    feeder_id TEXT NOT NULL,
    event_start TEXT,
    event_end TEXT,
    duration_min REAL,
    cause TEXT,
    breaker_status TEXT,
    voltage_before_kv REAL,
    voltage_after_kv REAL,
    FOREIGN KEY (feeder_id) REFERENCES dim_feeder(feeder_id)
);

CREATE TABLE oms_outage_reports_raw (
    oms_report_id TEXT PRIMARY KEY,
    linked_scada_event_id TEXT,
    source_system TEXT,
    company_name TEXT NOT NULL,
    feeder_id TEXT NOT NULL,
    outage_date TEXT,
    customers_interrupted INTEGER,
    reported_duration_min REAL,
    planned_flag INTEGER,
    complaints_count INTEGER,
    FOREIGN KEY (feeder_id) REFERENCES dim_feeder(feeder_id)
);

CREATE TABLE monthly_energy_balance_raw (
    month TEXT NOT NULL,
    company_name TEXT NOT NULL,
    feeder_id TEXT NOT NULL,
    energy_injected_mwh REAL,
    energy_billed_mwh REAL,
    estimated_technical_loss_mwh REAL,
    PRIMARY KEY (month, feeder_id),
    FOREIGN KEY (feeder_id) REFERENCES dim_feeder(feeder_id)
);

CREATE TABLE billing_collection_raw (
    month TEXT NOT NULL,
    company_name TEXT NOT NULL,
    feeder_id TEXT NOT NULL,
    revenue_billed_egp_m REAL,
    revenue_collected_egp_m REAL,
    billing_records_count INTEGER,
    billing_error_count INTEGER,
    PRIMARY KEY (month, feeder_id),
    FOREIGN KEY (feeder_id) REFERENCES dim_feeder(feeder_id)
);

CREATE TABLE meter_reading_quality_raw (
    month TEXT NOT NULL,
    company_name TEXT NOT NULL,
    feeder_id TEXT NOT NULL,
    expected_meter_reads INTEGER,
    actual_meter_reads INTEGER,
    estimated_reads INTEGER,
    manual_corrections INTEGER,
    PRIMARY KEY (month, feeder_id),
    FOREIGN KEY (feeder_id) REFERENCES dim_feeder(feeder_id)
);

CREATE TABLE scada_events_validated (
    scada_event_id TEXT PRIMARY KEY,
    source_system TEXT,
    company_name TEXT NOT NULL,
    feeder_id TEXT NOT NULL,
    event_start TEXT,
    event_end TEXT,
    duration_min REAL,
    cause TEXT,
    breaker_status TEXT,
    voltage_before_kv REAL,
    voltage_after_kv REAL,
    validation_flag TEXT,
    month TEXT,
    FOREIGN KEY (feeder_id) REFERENCES dim_feeder(feeder_id)
);

CREATE TABLE oms_reports_validated (
    oms_report_id TEXT PRIMARY KEY,
    linked_scada_event_id TEXT,
    source_system TEXT,
    company_name TEXT NOT NULL,
    feeder_id TEXT NOT NULL,
    outage_date TEXT,
    customers_interrupted INTEGER,
    reported_duration_min REAL,
    planned_flag INTEGER,
    complaints_count INTEGER,
    validation_flag TEXT,
    month TEXT,
    FOREIGN KEY (feeder_id) REFERENCES dim_feeder(feeder_id)
);

CREATE TABLE fact_monthly_outages (
    month TEXT NOT NULL,
    company_name TEXT NOT NULL,
    region_type TEXT,
    outage_events INTEGER,
    interrupted_customers INTEGER,
    customer_minutes_interrupted REAL,
    planned_events INTEGER,
    complaints_count INTEGER,
    total_customers INTEGER,
    feeder_count INTEGER,
    PRIMARY KEY (month, company_name)
);

CREATE TABLE fact_monthly_commercial (
    month TEXT NOT NULL,
    company_name TEXT NOT NULL,
    region_type TEXT,
    energy_injected_mwh REAL,
    energy_billed_mwh REAL,
    estimated_technical_loss_mwh REAL,
    revenue_billed_egp_m REAL,
    revenue_collected_egp_m REAL,
    expected_meter_reads INTEGER,
    actual_meter_reads INTEGER,
    estimated_reads INTEGER,
    manual_corrections INTEGER,
    billing_records_count INTEGER,
    billing_error_count INTEGER,
    total_customers INTEGER,
    PRIMARY KEY (month, company_name)
);

CREATE TABLE kpi_monthly_company (
    month TEXT NOT NULL,
    company_name TEXT NOT NULL,
    region_type TEXT,
    outage_events INTEGER,
    interrupted_customers INTEGER,
    customer_minutes_interrupted REAL,
    planned_events INTEGER,
    complaints_count INTEGER,
    total_customers INTEGER,
    feeder_count INTEGER,
    energy_injected_mwh REAL,
    energy_billed_mwh REAL,
    estimated_technical_loss_mwh REAL,
    revenue_billed_egp_m REAL,
    revenue_collected_egp_m REAL,
    expected_meter_reads INTEGER,
    actual_meter_reads INTEGER,
    estimated_reads INTEGER,
    manual_corrections INTEGER,
    billing_records_count INTEGER,
    billing_error_count INTEGER,
    saidi_hours_per_customer REAL,
    saifi_interruptions_per_customer REAL,
    caidi_minutes_per_interruption REAL,
    total_loss_pct REAL,
    technical_loss_pct REAL,
    non_technical_loss_pct REAL,
    collection_efficiency_pct REAL,
    meter_read_completeness_pct REAL,
    billing_error_rate_pct REAL,
    scada_validity_pct REAL,
    oms_validity_pct REAL,
    data_quality_score_pct REAL,
    management_flag TEXT,
    PRIMARY KEY (month, company_name)
);

CREATE TABLE benchmark_distribution_companies (
    company_name TEXT PRIMARY KEY,
    region_type TEXT,
    saidi_ytd REAL,
    saifi_avg REAL,
    caidi_avg REAL,
    total_loss_pct_avg REAL,
    non_technical_loss_pct_avg REAL,
    collection_efficiency_pct_avg REAL,
    meter_read_completeness_pct_avg REAL,
    data_quality_score_pct_avg REAL,
    saidi_ytd_rank REAL,
    total_loss_pct_avg_rank REAL,
    non_technical_loss_pct_avg_rank REAL,
    collection_efficiency_pct_avg_rank REAL,
    data_quality_score_pct_avg_rank REAL,
    benchmark_score REAL,
    overall_rank INTEGER
);

CREATE INDEX idx_scada_company_month ON scada_events_validated(company_name, month);
CREATE INDEX idx_oms_company_month ON oms_reports_validated(company_name, month);
CREATE INDEX idx_kpi_company_month ON kpi_monthly_company(company_name, month);
CREATE INDEX idx_kpi_flag ON kpi_monthly_company(management_flag);

CREATE VIEW vw_company_monthly_kpis AS
SELECT
    month,
    company_name,
    region_type,
    saidi_hours_per_customer,
    saifi_interruptions_per_customer,
    caidi_minutes_per_interruption,
    total_loss_pct,
    technical_loss_pct,
    non_technical_loss_pct,
    collection_efficiency_pct,
    meter_read_completeness_pct,
    data_quality_score_pct,
    management_flag
FROM kpi_monthly_company;

CREATE VIEW vw_company_benchmark AS
SELECT
    overall_rank,
    company_name,
    region_type,
    saidi_ytd,
    saifi_avg,
    total_loss_pct_avg,
    non_technical_loss_pct_avg,
    collection_efficiency_pct_avg,
    data_quality_score_pct_avg,
    benchmark_score
FROM benchmark_distribution_companies
ORDER BY overall_rank;

CREATE VIEW vw_data_quality_summary AS
SELECT
    company_name,
    AVG(scada_validity_pct) AS avg_scada_validity_pct,
    AVG(oms_validity_pct) AS avg_oms_validity_pct,
    AVG(meter_read_completeness_pct) AS avg_meter_read_completeness_pct,
    AVG(billing_error_rate_pct) AS avg_billing_error_rate_pct,
    AVG(data_quality_score_pct) AS avg_data_quality_score_pct
FROM kpi_monthly_company
GROUP BY company_name;
