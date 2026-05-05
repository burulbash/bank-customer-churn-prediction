DROP SCHEMA IF EXISTS raw CASCADE;
DROP SCHEMA IF EXISTS mart CASCADE;

CREATE SCHEMA raw;
CREATE SCHEMA mart;

CREATE TABLE raw.clients (
    client_id BIGINT PRIMARY KEY,
    registration_date DATE NOT NULL,
    birth_date DATE NOT NULL,
    gender VARCHAR(1),
    region VARCHAR(50),
    city_type VARCHAR(50),
    income_group VARCHAR(50),
    employment_type VARCHAR(50),
    customer_segment VARCHAR(50),
    salary_project_flag INTEGER,
    digital_adoption_level VARCHAR(50),
    estimated_monthly_income NUMERIC(14, 2),
    latent_behavior_type VARCHAR(50),
    churn_start_date DATE
);

CREATE TABLE raw.products (
    product_id BIGINT PRIMARY KEY,
    client_id BIGINT NOT NULL,
    product_type VARCHAR(50),
    open_date DATE,
    close_date DATE,
    status VARCHAR(50),
    monthly_fee NUMERIC(14, 2)
);

CREATE TABLE raw.transactions (
    transaction_id BIGINT PRIMARY KEY,
    client_id BIGINT NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_type VARCHAR(50),
    amount NUMERIC(16, 2),
    channel VARCHAR(50),
    merchant_category VARCHAR(50),
    is_successful INTEGER
);

CREATE TABLE raw.app_events (
    event_id BIGINT PRIMARY KEY,
    client_id BIGINT NOT NULL,
    event_date DATE NOT NULL,
    event_type VARCHAR(50),
    device_type VARCHAR(50),
    session_id BIGINT
);

CREATE TABLE raw.support_tickets (
    ticket_id BIGINT PRIMARY KEY,
    client_id BIGINT NOT NULL,
    ticket_date DATE NOT NULL,
    ticket_type VARCHAR(50),
    status VARCHAR(50),
    priority VARCHAR(50),
    satisfaction_score INTEGER
);

CREATE TABLE raw.marketing_contacts (
    contact_id BIGINT PRIMARY KEY,
    client_id BIGINT NOT NULL,
    contact_date DATE NOT NULL,
    campaign_type VARCHAR(50),
    channel VARCHAR(50),
    offer_type VARCHAR(50),
    opened_flag INTEGER,
    clicked_flag INTEGER
);

CREATE TABLE raw.customer_value_monthly (
    client_id BIGINT NOT NULL,
    month DATE NOT NULL,
    estimated_revenue NUMERIC(16, 2),
    estimated_cost NUMERIC(16, 2),
    net_value NUMERIC(16, 2),
    balance_avg NUMERIC(16, 2)
);

CREATE TABLE raw.macro_calendar (
    month DATE PRIMARY KEY,
    is_holiday_season INTEGER,
    salary_payment_period INTEGER,
    campaign_pressure_index NUMERIC(10, 4)
);
