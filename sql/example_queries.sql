
-- Example 1: Executive monthly KPI view
SELECT *
FROM vw_company_monthly_kpis
WHERE company_name = 'North Cairo'
ORDER BY month;

-- Example 2: Worst companies by YTD SAIDI
SELECT company_name, region_type, saidi_ytd, total_loss_pct_avg, data_quality_score_pct_avg
FROM vw_company_benchmark
ORDER BY saidi_ytd DESC;

-- Example 3: Months with high losses
SELECT month, company_name, total_loss_pct, non_technical_loss_pct, management_flag
FROM kpi_monthly_company
WHERE total_loss_pct > 18
ORDER BY total_loss_pct DESC;

-- Example 4: Data quality audit summary
SELECT *
FROM vw_data_quality_summary
ORDER BY avg_data_quality_score_pct ASC;

-- Example 5: Raw-to-KPI lineage for a company/month
SELECT
    k.company_name,
    k.month,
    k.saidi_hours_per_customer,
    o.outage_events,
    o.customer_minutes_interrupted,
    c.energy_injected_mwh,
    c.energy_billed_mwh,
    k.total_loss_pct
FROM kpi_monthly_company k
JOIN fact_monthly_outages o
  ON k.company_name = o.company_name AND k.month = o.month
JOIN fact_monthly_commercial c
  ON k.company_name = c.company_name AND k.month = c.month
WHERE k.company_name = 'Alexandria'
  AND k.month = '2025-07';
