DROP TABLE IF EXISTS mart.churn_feature_table;

CREATE TABLE mart.churn_feature_table AS
WITH snapshot_dates AS (
    SELECT generate_series(
        DATE '2024-01-01',
        DATE '2025-10-01',
        INTERVAL '1 month'
    )::date AS snapshot_date
),

base AS (
    SELECT
        c.client_id,
        s.snapshot_date,

        c.registration_date,
        c.birth_date,
        c.gender,
        c.region,
        c.city_type,
        c.income_group,
        c.employment_type,
        c.customer_segment,
        c.salary_project_flag,
        c.digital_adoption_level,
        c.estimated_monthly_income,

        EXTRACT(YEAR FROM AGE(s.snapshot_date, c.birth_date))::integer AS client_age,
        (s.snapshot_date - c.registration_date)::integer AS client_tenure_days

    FROM raw.clients c
    CROSS JOIN snapshot_dates s
    WHERE c.registration_date < s.snapshot_date
),

feature_rows AS (
    SELECT
        b.client_id,
        b.snapshot_date,

        -- Static / client features
        b.client_age,
        b.client_tenure_days,
        b.gender,
        b.region,
        b.city_type,
        b.income_group,
        b.employment_type,
        b.customer_segment,
        b.salary_project_flag,
        b.digital_adoption_level,
        b.estimated_monthly_income,

        -- Product features
        COALESCE(pr.active_products_count, 0) AS active_products_count,
        COALESCE(pr.closed_products_count, 0) AS closed_products_count,
        COALESCE(pr.product_diversity_score, 0) AS product_diversity_score,

        COALESCE(pr.has_debit_card, 0) AS has_debit_card,
        COALESCE(pr.has_credit_card, 0) AS has_credit_card,
        COALESCE(pr.has_deposit, 0) AS has_deposit,
        COALESCE(pr.has_loan, 0) AS has_loan,
        COALESCE(pr.has_mobile_app, 0) AS has_mobile_app,
        COALESCE(pr.has_savings_account, 0) AS has_savings_account,

        pr.days_since_last_product_open,
        pr.days_since_last_product_close,

        -- Transaction features
        COALESCE(tx.txn_count_30d, 0) AS txn_count_30d,
        COALESCE(tx.txn_count_60d, 0) AS txn_count_60d,
        COALESCE(tx.txn_count_90d, 0) AS txn_count_90d,
        COALESCE(tx.txn_count_180d, 0) AS txn_count_180d,

        COALESCE(tx.txn_sum_30d, 0)::double precision AS txn_sum_30d,
        COALESCE(tx.txn_sum_60d, 0)::double precision AS txn_sum_60d,
        COALESCE(tx.txn_sum_90d, 0)::double precision AS txn_sum_90d,
        COALESCE(tx.txn_sum_180d, 0)::double precision AS txn_sum_180d,

        tx.txn_avg_amount_30d::double precision AS txn_avg_amount_30d,
        tx.txn_avg_amount_90d::double precision AS txn_avg_amount_90d,
        tx.txn_max_amount_90d::double precision AS txn_max_amount_90d,

        tx.successful_txn_rate_90d::double precision AS successful_txn_rate_90d,
        COALESCE(tx.failed_txn_count_90d, 0) AS failed_txn_count_90d,

        COALESCE(tx.active_txn_days_30d, 0) AS active_txn_days_30d,
        COALESCE(tx.active_txn_days_90d, 0) AS active_txn_days_90d,
        tx.days_since_last_txn,

        COALESCE(tx.cash_withdrawal_count_90d, 0) AS cash_withdrawal_count_90d,
        COALESCE(tx.card_purchase_count_90d, 0) AS card_purchase_count_90d,
        COALESCE(tx.p2p_transfer_count_90d, 0) AS p2p_transfer_count_90d,
        COALESCE(tx.utility_payment_count_90d, 0) AS utility_payment_count_90d,

        tx.mobile_txn_share_90d::double precision AS mobile_txn_share_90d,
        tx.atm_txn_share_90d::double precision AS atm_txn_share_90d,
        tx.branch_txn_share_90d::double precision AS branch_txn_share_90d,

        COALESCE(tx.txn_count_last30, 0) AS txn_count_last30,
        COALESCE(tx.txn_count_prev30, 0) AS txn_count_prev30,
        COALESCE(tx.txn_count_last30, 0) - COALESCE(tx.txn_count_prev30, 0) AS txn_count_change_30d,

        CASE
            WHEN COALESCE(tx.txn_count_prev30, 0) > 0
            THEN (COALESCE(tx.txn_count_last30, 0) - COALESCE(tx.txn_count_prev30, 0))::double precision
                 / NULLIF(tx.txn_count_prev30, 0)
            ELSE COALESCE(tx.txn_count_last30, 0)::double precision
        END AS txn_count_change_pct_30d,

        COALESCE(tx.txn_sum_last30, 0)::double precision AS txn_sum_last30,
        COALESCE(tx.txn_sum_prev30, 0)::double precision AS txn_sum_prev30,
        (COALESCE(tx.txn_sum_last30, 0) - COALESCE(tx.txn_sum_prev30, 0))::double precision AS txn_sum_change_30d,

        CASE
            WHEN COALESCE(tx.txn_sum_prev30, 0) > 0
            THEN (COALESCE(tx.txn_sum_last30, 0) - COALESCE(tx.txn_sum_prev30, 0))::double precision
                 / NULLIF(tx.txn_sum_prev30, 0)
            ELSE COALESCE(tx.txn_sum_last30, 0)::double precision
        END AS txn_sum_change_pct_30d,

        -- App features
        COALESCE(app.app_login_count_30d, 0) AS app_login_count_30d,
        COALESCE(app.app_login_count_60d, 0) AS app_login_count_60d,
        COALESCE(app.app_login_count_90d, 0) AS app_login_count_90d,
        COALESCE(app.app_events_count_30d, 0) AS app_events_count_30d,
        COALESCE(app.app_events_count_90d, 0) AS app_events_count_90d,
        COALESCE(app.unique_app_event_types_90d, 0) AS unique_app_event_types_90d,
        COALESCE(app.active_app_days_90d, 0) AS active_app_days_90d,

        app.days_since_last_app_login,
        app.days_since_last_app_event,

        COALESCE(app.transfer_created_count_90d, 0) AS transfer_created_count_90d,
        COALESCE(app.payment_created_count_90d, 0) AS payment_created_count_90d,
        COALESCE(app.balance_view_count_90d, 0) AS balance_view_count_90d,
        COALESCE(app.support_chat_opened_count_90d, 0) AS support_chat_opened_count_90d,
        COALESCE(app.loan_offer_view_count_90d, 0) AS loan_offer_view_count_90d,

        COALESCE(app.app_login_last30, 0) AS app_login_last30,
        COALESCE(app.app_login_prev30, 0) AS app_login_prev30,
        COALESCE(app.app_login_last30, 0) - COALESCE(app.app_login_prev30, 0) AS app_login_change_30d,

        CASE
            WHEN COALESCE(app.app_login_prev30, 0) > 0
            THEN (COALESCE(app.app_login_last30, 0) - COALESCE(app.app_login_prev30, 0))::double precision
                 / NULLIF(app.app_login_prev30, 0)
            ELSE COALESCE(app.app_login_last30, 0)::double precision
        END AS app_login_change_pct_30d,

        -- Support features
        COALESCE(st.tickets_count_30d, 0) AS tickets_count_30d,
        COALESCE(st.tickets_count_90d, 0) AS tickets_count_90d,
        COALESCE(st.complaints_count_90d, 0) AS complaints_count_90d,
        COALESCE(st.critical_tickets_count_90d, 0) AS critical_tickets_count_90d,
        COALESCE(st.open_tickets_count, 0) AS open_tickets_count,
        COALESCE(st.escalated_tickets_count_90d, 0) AS escalated_tickets_count_90d,
        st.avg_satisfaction_score_90d::double precision AS avg_satisfaction_score_90d,
        st.min_satisfaction_score_90d,
        st.days_since_last_ticket,
        st.days_since_last_complaint,

        -- Marketing features
        COALESCE(mc.marketing_contacts_30d, 0) AS marketing_contacts_30d,
        COALESCE(mc.marketing_contacts_90d, 0) AS marketing_contacts_90d,
        COALESCE(mc.retention_contacts_90d, 0) AS retention_contacts_90d,
        mc.campaign_open_rate_90d::double precision AS campaign_open_rate_90d,
        mc.campaign_click_rate_90d::double precision AS campaign_click_rate_90d,
        COALESCE(mc.push_contacts_90d, 0) AS push_contacts_90d,
        COALESCE(mc.sms_contacts_90d, 0) AS sms_contacts_90d,
        COALESCE(mc.email_contacts_90d, 0) AS email_contacts_90d,
        COALESCE(mc.call_contacts_90d, 0) AS call_contacts_90d,
        mc.days_since_last_marketing_contact,

        -- Value features
        COALESCE(cv.estimated_revenue_3m, 0)::double precision AS estimated_revenue_3m,
        COALESCE(cv.estimated_revenue_6m, 0)::double precision AS estimated_revenue_6m,
        COALESCE(cv.estimated_cost_3m, 0)::double precision AS estimated_cost_3m,
        COALESCE(cv.net_value_3m, 0)::double precision AS net_value_3m,
        COALESCE(cv.avg_balance_3m, 0)::double precision AS avg_balance_3m,
        COALESCE(cv.avg_balance_6m, 0)::double precision AS avg_balance_6m,

        CASE
            WHEN COALESCE(cv.net_value_3m, 0) >= 35000 THEN 'premium_value'
            WHEN COALESCE(cv.net_value_3m, 0) >= 15000 THEN 'high_value'
            WHEN COALESCE(cv.net_value_3m, 0) >= 5000 THEN 'medium_value'
            ELSE 'low_value'
        END AS value_segment,

        -- Target helper columns. These are not model features.
        COALESCE(tx.future_txn_count_60d, 0) AS future_txn_count_60d,
        COALESCE(app.future_app_login_count_60d, 0) AS future_app_login_count_60d,
        COALESCE(pr.future_product_open_count_60d, 0) AS future_product_open_count_60d,

        CASE
            WHEN COALESCE(tx.future_txn_count_60d, 0) = 0
             AND COALESCE(app.future_app_login_count_60d, 0) = 0
             AND COALESCE(pr.future_product_open_count_60d, 0) = 0
            THEN 1
            ELSE 0
        END AS target_churn_60d

    FROM base b

    LEFT JOIN LATERAL (
        SELECT
            COUNT(*) FILTER (
                WHERE p.open_date < b.snapshot_date
                  AND (p.close_date IS NULL OR p.close_date >= b.snapshot_date)
                  AND p.status = 'active'
            ) AS active_products_count,

            COUNT(*) FILTER (
                WHERE p.close_date < b.snapshot_date
            ) AS closed_products_count,

            COUNT(DISTINCT p.product_type) FILTER (
                WHERE p.open_date < b.snapshot_date
                  AND (p.close_date IS NULL OR p.close_date >= b.snapshot_date)
                  AND p.status = 'active'
            ) AS product_diversity_score,

            MAX(CASE WHEN p.product_type = 'debit_card'
                      AND p.open_date < b.snapshot_date
                      AND (p.close_date IS NULL OR p.close_date >= b.snapshot_date)
                      AND p.status = 'active' THEN 1 ELSE 0 END) AS has_debit_card,

            MAX(CASE WHEN p.product_type = 'credit_card'
                      AND p.open_date < b.snapshot_date
                      AND (p.close_date IS NULL OR p.close_date >= b.snapshot_date)
                      AND p.status = 'active' THEN 1 ELSE 0 END) AS has_credit_card,

            MAX(CASE WHEN p.product_type = 'deposit'
                      AND p.open_date < b.snapshot_date
                      AND (p.close_date IS NULL OR p.close_date >= b.snapshot_date)
                      AND p.status = 'active' THEN 1 ELSE 0 END) AS has_deposit,

            MAX(CASE WHEN p.product_type = 'loan'
                      AND p.open_date < b.snapshot_date
                      AND (p.close_date IS NULL OR p.close_date >= b.snapshot_date)
                      AND p.status = 'active' THEN 1 ELSE 0 END) AS has_loan,

            MAX(CASE WHEN p.product_type = 'mobile_app'
                      AND p.open_date < b.snapshot_date
                      AND (p.close_date IS NULL OR p.close_date >= b.snapshot_date)
                      AND p.status = 'active' THEN 1 ELSE 0 END) AS has_mobile_app,

            MAX(CASE WHEN p.product_type = 'savings_account'
                      AND p.open_date < b.snapshot_date
                      AND (p.close_date IS NULL OR p.close_date >= b.snapshot_date)
                      AND p.status = 'active' THEN 1 ELSE 0 END) AS has_savings_account,

            b.snapshot_date - MAX(p.open_date) FILTER (
                WHERE p.open_date < b.snapshot_date
            ) AS days_since_last_product_open,

            b.snapshot_date - MAX(p.close_date) FILTER (
                WHERE p.close_date < b.snapshot_date
            ) AS days_since_last_product_close,

            COUNT(*) FILTER (
                WHERE p.open_date > b.snapshot_date
                  AND p.open_date <= b.snapshot_date + INTERVAL '60 days'
            ) AS future_product_open_count_60d

        FROM raw.products p
        WHERE p.client_id = b.client_id
          AND p.open_date <= b.snapshot_date + INTERVAL '60 days'
    ) pr ON TRUE

    LEFT JOIN LATERAL (
        SELECT
            COUNT(*) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '30 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.is_successful = 1
            ) AS txn_count_30d,

            COUNT(*) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '60 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.is_successful = 1
            ) AS txn_count_60d,

            COUNT(*) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '90 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.is_successful = 1
            ) AS txn_count_90d,

            COUNT(*) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '180 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.is_successful = 1
            ) AS txn_count_180d,

            SUM(t.amount) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '30 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.is_successful = 1
            ) AS txn_sum_30d,

            SUM(t.amount) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '60 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.is_successful = 1
            ) AS txn_sum_60d,

            SUM(t.amount) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '90 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.is_successful = 1
            ) AS txn_sum_90d,

            SUM(t.amount) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '180 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.is_successful = 1
            ) AS txn_sum_180d,

            AVG(t.amount) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '30 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.is_successful = 1
            ) AS txn_avg_amount_30d,

            AVG(t.amount) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '90 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.is_successful = 1
            ) AS txn_avg_amount_90d,

            MAX(t.amount) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '90 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.is_successful = 1
            ) AS txn_max_amount_90d,

            COUNT(*) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '90 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.is_successful = 1
            )::double precision
            / NULLIF(
                COUNT(*) FILTER (
                    WHERE t.transaction_date >= b.snapshot_date - INTERVAL '90 days'
                      AND t.transaction_date < b.snapshot_date
                ),
                0
            ) AS successful_txn_rate_90d,

            COUNT(*) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '90 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.is_successful = 0
            ) AS failed_txn_count_90d,

            COUNT(DISTINCT t.transaction_date) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '30 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.is_successful = 1
            ) AS active_txn_days_30d,

            COUNT(DISTINCT t.transaction_date) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '90 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.is_successful = 1
            ) AS active_txn_days_90d,

            b.snapshot_date - MAX(t.transaction_date) FILTER (
                WHERE t.transaction_date < b.snapshot_date
                  AND t.is_successful = 1
            ) AS days_since_last_txn,

            COUNT(*) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '90 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.transaction_type = 'cash_withdrawal'
                  AND t.is_successful = 1
            ) AS cash_withdrawal_count_90d,

            COUNT(*) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '90 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.transaction_type = 'card_purchase'
                  AND t.is_successful = 1
            ) AS card_purchase_count_90d,

            COUNT(*) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '90 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.transaction_type = 'p2p_transfer'
                  AND t.is_successful = 1
            ) AS p2p_transfer_count_90d,

            COUNT(*) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '90 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.transaction_type = 'utility_payment'
                  AND t.is_successful = 1
            ) AS utility_payment_count_90d,

            COUNT(*) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '90 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.channel = 'mobile_app'
                  AND t.is_successful = 1
            )::double precision
            / NULLIF(
                COUNT(*) FILTER (
                    WHERE t.transaction_date >= b.snapshot_date - INTERVAL '90 days'
                      AND t.transaction_date < b.snapshot_date
                      AND t.is_successful = 1
                ),
                0
            ) AS mobile_txn_share_90d,

            COUNT(*) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '90 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.channel = 'atm'
                  AND t.is_successful = 1
            )::double precision
            / NULLIF(
                COUNT(*) FILTER (
                    WHERE t.transaction_date >= b.snapshot_date - INTERVAL '90 days'
                      AND t.transaction_date < b.snapshot_date
                      AND t.is_successful = 1
                ),
                0
            ) AS atm_txn_share_90d,

            COUNT(*) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '90 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.channel = 'branch'
                  AND t.is_successful = 1
            )::double precision
            / NULLIF(
                COUNT(*) FILTER (
                    WHERE t.transaction_date >= b.snapshot_date - INTERVAL '90 days'
                      AND t.transaction_date < b.snapshot_date
                      AND t.is_successful = 1
                ),
                0
            ) AS branch_txn_share_90d,

            COUNT(*) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '30 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.is_successful = 1
            ) AS txn_count_last30,

            COUNT(*) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '60 days'
                  AND t.transaction_date < b.snapshot_date - INTERVAL '30 days'
                  AND t.is_successful = 1
            ) AS txn_count_prev30,

            SUM(t.amount) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '30 days'
                  AND t.transaction_date < b.snapshot_date
                  AND t.is_successful = 1
            ) AS txn_sum_last30,

            SUM(t.amount) FILTER (
                WHERE t.transaction_date >= b.snapshot_date - INTERVAL '60 days'
                  AND t.transaction_date < b.snapshot_date - INTERVAL '30 days'
                  AND t.is_successful = 1
            ) AS txn_sum_prev30,

            COUNT(*) FILTER (
                WHERE t.transaction_date > b.snapshot_date
                  AND t.transaction_date <= b.snapshot_date + INTERVAL '60 days'
                  AND t.is_successful = 1
            ) AS future_txn_count_60d

        FROM raw.transactions t
        WHERE t.client_id = b.client_id
          AND t.transaction_date >= b.snapshot_date - INTERVAL '180 days'
          AND t.transaction_date <= b.snapshot_date + INTERVAL '60 days'
    ) tx ON TRUE

    LEFT JOIN LATERAL (
        SELECT
            COUNT(*) FILTER (
                WHERE e.event_date >= b.snapshot_date - INTERVAL '30 days'
                  AND e.event_date < b.snapshot_date
                  AND e.event_type = 'login'
            ) AS app_login_count_30d,

            COUNT(*) FILTER (
                WHERE e.event_date >= b.snapshot_date - INTERVAL '60 days'
                  AND e.event_date < b.snapshot_date
                  AND e.event_type = 'login'
            ) AS app_login_count_60d,

            COUNT(*) FILTER (
                WHERE e.event_date >= b.snapshot_date - INTERVAL '90 days'
                  AND e.event_date < b.snapshot_date
                  AND e.event_type = 'login'
            ) AS app_login_count_90d,

            COUNT(*) FILTER (
                WHERE e.event_date >= b.snapshot_date - INTERVAL '30 days'
                  AND e.event_date < b.snapshot_date
            ) AS app_events_count_30d,

            COUNT(*) FILTER (
                WHERE e.event_date >= b.snapshot_date - INTERVAL '90 days'
                  AND e.event_date < b.snapshot_date
            ) AS app_events_count_90d,

            COUNT(DISTINCT e.event_type) FILTER (
                WHERE e.event_date >= b.snapshot_date - INTERVAL '90 days'
                  AND e.event_date < b.snapshot_date
            ) AS unique_app_event_types_90d,

            COUNT(DISTINCT e.event_date) FILTER (
                WHERE e.event_date >= b.snapshot_date - INTERVAL '90 days'
                  AND e.event_date < b.snapshot_date
            ) AS active_app_days_90d,

            b.snapshot_date - MAX(e.event_date) FILTER (
                WHERE e.event_date < b.snapshot_date
                  AND e.event_type = 'login'
            ) AS days_since_last_app_login,

            b.snapshot_date - MAX(e.event_date) FILTER (
                WHERE e.event_date < b.snapshot_date
            ) AS days_since_last_app_event,

            COUNT(*) FILTER (
                WHERE e.event_date >= b.snapshot_date - INTERVAL '90 days'
                  AND e.event_date < b.snapshot_date
                  AND e.event_type = 'transfer_created'
            ) AS transfer_created_count_90d,

            COUNT(*) FILTER (
                WHERE e.event_date >= b.snapshot_date - INTERVAL '90 days'
                  AND e.event_date < b.snapshot_date
                  AND e.event_type = 'payment_created'
            ) AS payment_created_count_90d,

            COUNT(*) FILTER (
                WHERE e.event_date >= b.snapshot_date - INTERVAL '90 days'
                  AND e.event_date < b.snapshot_date
                  AND e.event_type = 'balance_view'
            ) AS balance_view_count_90d,

            COUNT(*) FILTER (
                WHERE e.event_date >= b.snapshot_date - INTERVAL '90 days'
                  AND e.event_date < b.snapshot_date
                  AND e.event_type = 'support_chat_opened'
            ) AS support_chat_opened_count_90d,

            COUNT(*) FILTER (
                WHERE e.event_date >= b.snapshot_date - INTERVAL '90 days'
                  AND e.event_date < b.snapshot_date
                  AND e.event_type = 'loan_offer_view'
            ) AS loan_offer_view_count_90d,

            COUNT(*) FILTER (
                WHERE e.event_date >= b.snapshot_date - INTERVAL '30 days'
                  AND e.event_date < b.snapshot_date
                  AND e.event_type = 'login'
            ) AS app_login_last30,

            COUNT(*) FILTER (
                WHERE e.event_date >= b.snapshot_date - INTERVAL '60 days'
                  AND e.event_date < b.snapshot_date - INTERVAL '30 days'
                  AND e.event_type = 'login'
            ) AS app_login_prev30,

            COUNT(*) FILTER (
                WHERE e.event_date > b.snapshot_date
                  AND e.event_date <= b.snapshot_date + INTERVAL '60 days'
                  AND e.event_type = 'login'
            ) AS future_app_login_count_60d

        FROM raw.app_events e
        WHERE e.client_id = b.client_id
          AND e.event_date >= b.snapshot_date - INTERVAL '90 days'
          AND e.event_date <= b.snapshot_date + INTERVAL '60 days'
    ) app ON TRUE

    LEFT JOIN LATERAL (
        SELECT
            COUNT(*) FILTER (
                WHERE st.ticket_date >= b.snapshot_date - INTERVAL '30 days'
                  AND st.ticket_date < b.snapshot_date
            ) AS tickets_count_30d,

            COUNT(*) FILTER (
                WHERE st.ticket_date >= b.snapshot_date - INTERVAL '90 days'
                  AND st.ticket_date < b.snapshot_date
            ) AS tickets_count_90d,

            COUNT(*) FILTER (
                WHERE st.ticket_date >= b.snapshot_date - INTERVAL '90 days'
                  AND st.ticket_date < b.snapshot_date
                  AND st.ticket_type = 'complaint'
            ) AS complaints_count_90d,

            COUNT(*) FILTER (
                WHERE st.ticket_date >= b.snapshot_date - INTERVAL '90 days'
                  AND st.ticket_date < b.snapshot_date
                  AND st.priority = 'critical'
            ) AS critical_tickets_count_90d,

            COUNT(*) FILTER (
                WHERE st.ticket_date < b.snapshot_date
                  AND st.status = 'open'
            ) AS open_tickets_count,

            COUNT(*) FILTER (
                WHERE st.ticket_date >= b.snapshot_date - INTERVAL '90 days'
                  AND st.ticket_date < b.snapshot_date
                  AND st.status = 'escalated'
            ) AS escalated_tickets_count_90d,

            AVG(st.satisfaction_score) FILTER (
                WHERE st.ticket_date >= b.snapshot_date - INTERVAL '90 days'
                  AND st.ticket_date < b.snapshot_date
            ) AS avg_satisfaction_score_90d,

            MIN(st.satisfaction_score) FILTER (
                WHERE st.ticket_date >= b.snapshot_date - INTERVAL '90 days'
                  AND st.ticket_date < b.snapshot_date
            ) AS min_satisfaction_score_90d,

            b.snapshot_date - MAX(st.ticket_date) FILTER (
                WHERE st.ticket_date < b.snapshot_date
            ) AS days_since_last_ticket,

            b.snapshot_date - MAX(st.ticket_date) FILTER (
                WHERE st.ticket_date < b.snapshot_date
                  AND st.ticket_type = 'complaint'
            ) AS days_since_last_complaint

        FROM raw.support_tickets st
        WHERE st.client_id = b.client_id
          AND st.ticket_date < b.snapshot_date
    ) st ON TRUE

    LEFT JOIN LATERAL (
        SELECT
            COUNT(*) FILTER (
                WHERE mc.contact_date >= b.snapshot_date - INTERVAL '30 days'
                  AND mc.contact_date < b.snapshot_date
            ) AS marketing_contacts_30d,

            COUNT(*) FILTER (
                WHERE mc.contact_date >= b.snapshot_date - INTERVAL '90 days'
                  AND mc.contact_date < b.snapshot_date
            ) AS marketing_contacts_90d,

            COUNT(*) FILTER (
                WHERE mc.contact_date >= b.snapshot_date - INTERVAL '90 days'
                  AND mc.contact_date < b.snapshot_date
                  AND mc.campaign_type = 'retention'
            ) AS retention_contacts_90d,

            AVG(mc.opened_flag) FILTER (
                WHERE mc.contact_date >= b.snapshot_date - INTERVAL '90 days'
                  AND mc.contact_date < b.snapshot_date
            ) AS campaign_open_rate_90d,

            AVG(mc.clicked_flag) FILTER (
                WHERE mc.contact_date >= b.snapshot_date - INTERVAL '90 days'
                  AND mc.contact_date < b.snapshot_date
            ) AS campaign_click_rate_90d,

            COUNT(*) FILTER (
                WHERE mc.contact_date >= b.snapshot_date - INTERVAL '90 days'
                  AND mc.contact_date < b.snapshot_date
                  AND mc.channel = 'push'
            ) AS push_contacts_90d,

            COUNT(*) FILTER (
                WHERE mc.contact_date >= b.snapshot_date - INTERVAL '90 days'
                  AND mc.contact_date < b.snapshot_date
                  AND mc.channel = 'sms'
            ) AS sms_contacts_90d,

            COUNT(*) FILTER (
                WHERE mc.contact_date >= b.snapshot_date - INTERVAL '90 days'
                  AND mc.contact_date < b.snapshot_date
                  AND mc.channel = 'email'
            ) AS email_contacts_90d,

            COUNT(*) FILTER (
                WHERE mc.contact_date >= b.snapshot_date - INTERVAL '90 days'
                  AND mc.contact_date < b.snapshot_date
                  AND mc.channel = 'call'
            ) AS call_contacts_90d,

            b.snapshot_date - MAX(mc.contact_date) FILTER (
                WHERE mc.contact_date < b.snapshot_date
            ) AS days_since_last_marketing_contact

        FROM raw.marketing_contacts mc
        WHERE mc.client_id = b.client_id
          AND mc.contact_date < b.snapshot_date
    ) mc ON TRUE

    LEFT JOIN LATERAL (
        SELECT
            SUM(cv.estimated_revenue) FILTER (
                WHERE cv.month >= DATE_TRUNC('month', b.snapshot_date)::date - INTERVAL '3 months'
                  AND cv.month < DATE_TRUNC('month', b.snapshot_date)::date
            ) AS estimated_revenue_3m,

            SUM(cv.estimated_revenue) FILTER (
                WHERE cv.month >= DATE_TRUNC('month', b.snapshot_date)::date - INTERVAL '6 months'
                  AND cv.month < DATE_TRUNC('month', b.snapshot_date)::date
            ) AS estimated_revenue_6m,

            SUM(cv.estimated_cost) FILTER (
                WHERE cv.month >= DATE_TRUNC('month', b.snapshot_date)::date - INTERVAL '3 months'
                  AND cv.month < DATE_TRUNC('month', b.snapshot_date)::date
            ) AS estimated_cost_3m,

            SUM(cv.net_value) FILTER (
                WHERE cv.month >= DATE_TRUNC('month', b.snapshot_date)::date - INTERVAL '3 months'
                  AND cv.month < DATE_TRUNC('month', b.snapshot_date)::date
            ) AS net_value_3m,

            AVG(cv.balance_avg) FILTER (
                WHERE cv.month >= DATE_TRUNC('month', b.snapshot_date)::date - INTERVAL '3 months'
                  AND cv.month < DATE_TRUNC('month', b.snapshot_date)::date
            ) AS avg_balance_3m,

            AVG(cv.balance_avg) FILTER (
                WHERE cv.month >= DATE_TRUNC('month', b.snapshot_date)::date - INTERVAL '6 months'
                  AND cv.month < DATE_TRUNC('month', b.snapshot_date)::date
            ) AS avg_balance_6m

        FROM raw.customer_value_monthly cv
        WHERE cv.client_id = b.client_id
          AND cv.month >= DATE_TRUNC('month', b.snapshot_date)::date - INTERVAL '6 months'
          AND cv.month < DATE_TRUNC('month', b.snapshot_date)::date
    ) cv ON TRUE
)

SELECT
    *,
    CASE
        WHEN txn_count_90d = 0 AND app_login_count_90d = 0 THEN 'inactive_recently'
        WHEN txn_count_change_pct_30d < -0.5 OR app_login_change_pct_30d < -0.5 THEN 'activity_drop'
        WHEN app_login_count_90d >= 15 THEN 'digital_active'
        WHEN txn_count_90d >= 15 THEN 'transaction_active'
        ELSE 'moderate_activity'
    END AS activity_segment,

    CASE
        WHEN complaints_count_90d > 0 OR avg_satisfaction_score_90d <= 2 THEN 'complaint_risk'
        ELSE 'no_recent_complaints'
    END AS complaint_segment,

    CASE
        WHEN digital_adoption_level = 'high' AND app_login_count_90d >= 15 THEN 'digital_power_user'
        WHEN digital_adoption_level = 'low' OR app_login_count_90d = 0 THEN 'low_digital_engagement'
        ELSE 'medium_digital_engagement'
    END AS digital_segment

FROM feature_rows

-- Eligibility rule:
-- we model churn only for customers who were active before snapshot_date.
WHERE txn_count_90d > 0
   OR app_login_count_90d > 0
   OR active_products_count > 0;

CREATE INDEX idx_churn_feature_table_client_snapshot
    ON mart.churn_feature_table(client_id, snapshot_date);

CREATE INDEX idx_churn_feature_table_snapshot
    ON mart.churn_feature_table(snapshot_date);

CREATE INDEX idx_churn_feature_table_target
    ON mart.churn_feature_table(target_churn_60d);

ANALYZE mart.churn_feature_table;
