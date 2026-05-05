-- Quality checks for mart.churn_feature_table

-- 1. General table summary
SELECT
    COUNT(*) AS rows_count,
    COUNT(DISTINCT client_id) AS unique_clients,
    MIN(snapshot_date) AS min_snapshot_date,
    MAX(snapshot_date) AS max_snapshot_date,
    AVG(target_churn_60d::numeric) AS churn_rate
FROM mart.churn_feature_table;


-- 2. Duplicate check: one row should be client_id + snapshot_date
SELECT
    COUNT(*) AS rows_count,
    COUNT(DISTINCT (client_id, snapshot_date)) AS unique_client_snapshots,
    COUNT(*) - COUNT(DISTINCT (client_id, snapshot_date)) AS duplicate_rows
FROM mart.churn_feature_table;


-- 3. Target distribution
SELECT
    target_churn_60d,
    COUNT(*) AS rows_count,
    COUNT(*)::numeric / SUM(COUNT(*)) OVER () AS share
FROM mart.churn_feature_table
GROUP BY target_churn_60d
ORDER BY target_churn_60d;


-- 4. Churn by customer segment
SELECT
    customer_segment,
    COUNT(*) AS rows_count,
    AVG(target_churn_60d::numeric) AS churn_rate
FROM mart.churn_feature_table
GROUP BY customer_segment
ORDER BY churn_rate DESC;


-- 5. Churn by activity segment
SELECT
    activity_segment,
    COUNT(*) AS rows_count,
    AVG(target_churn_60d::numeric) AS churn_rate
FROM mart.churn_feature_table
GROUP BY activity_segment
ORDER BY churn_rate DESC;


-- 6. Missing values in key fields
SELECT
    COUNT(*) FILTER (WHERE client_id IS NULL) AS null_client_id,
    COUNT(*) FILTER (WHERE snapshot_date IS NULL) AS null_snapshot_date,
    COUNT(*) FILTER (WHERE target_churn_60d IS NULL) AS null_target,
    COUNT(*) FILTER (WHERE txn_count_90d IS NULL) AS null_txn_count_90d,
    COUNT(*) FILTER (WHERE app_login_count_90d IS NULL) AS null_app_login_count_90d,
    COUNT(*) FILTER (WHERE active_products_count IS NULL) AS null_active_products_count
FROM mart.churn_feature_table;


-- 7. Age sanity check
SELECT
    COUNT(*) AS invalid_age_rows
FROM mart.churn_feature_table
WHERE client_age < 18 OR client_age > 90;


-- 8. Snapshot-level churn trend
SELECT
    snapshot_date,
    COUNT(*) AS rows_count,
    AVG(target_churn_60d::numeric) AS churn_rate
FROM mart.churn_feature_table
GROUP BY snapshot_date
ORDER BY snapshot_date;
