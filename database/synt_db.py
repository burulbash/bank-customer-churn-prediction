from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

START_DATE = pd.Timestamp("2023-01-01")
END_DATE = pd.Timestamp("2025-12-31")
MONTHS = pd.date_range(START_DATE, END_DATE, freq="MS")

SIZE_CONFIG = {
    "tiny": 2_000,
    "small": 10_000,
    "medium": 30_000,
}


BEHAVIOR_PROFILES = {
    "loyal_digital": {
        "txn_rate": 3.2,
        "app_rate": 7.5,
        "ticket_rate": 0.04,
        "marketing_response": 0.22,
        "churn_prob": 0.08,
    },
    "salary_client": {
        "txn_rate": 4.0,
        "app_rate": 4.5,
        "ticket_rate": 0.05,
        "marketing_response": 0.16,
        "churn_prob": 0.07,
    },
    "cash_user": {
        "txn_rate": 2.0,
        "app_rate": 1.0,
        "ticket_rate": 0.05,
        "marketing_response": 0.08,
        "churn_prob": 0.16,
    },
    "low_engagement": {
        "txn_rate": 0.9,
        "app_rate": 0.6,
        "ticket_rate": 0.06,
        "marketing_response": 0.06,
        "churn_prob": 0.30,
    },
    "complaint_prone": {
        "txn_rate": 1.8,
        "app_rate": 2.0,
        "ticket_rate": 0.22,
        "marketing_response": 0.07,
        "churn_prob": 0.27,
    },
    "campaign_sensitive": {
        "txn_rate": 2.4,
        "app_rate": 3.5,
        "ticket_rate": 0.06,
        "marketing_response": 0.34,
        "churn_prob": 0.15,
    },
    "high_value_busy": {
        "txn_rate": 5.0,
        "app_rate": 3.0,
        "ticket_rate": 0.08,
        "marketing_response": 0.18,
        "churn_prob": 0.12,
    },
    "young_mobile_first": {
        "txn_rate": 2.8,
        "app_rate": 8.5,
        "ticket_rate": 0.05,
        "marketing_response": 0.20,
        "churn_prob": 0.13,
    },
}


def random_dates(
    rng: np.random.Generator,
    start: pd.Timestamp,
    end: pd.Timestamp,
    size: int,
) -> pd.Series:
    start_day = start.toordinal()
    end_day = end.toordinal()
    days = rng.integers(start_day, end_day + 1, size=size)
    return pd.to_datetime([pd.Timestamp.fromordinal(int(day)) for day in days])


def month_end(month_start: pd.Timestamp) -> pd.Timestamp:
    return month_start + pd.offsets.MonthEnd(0)


def generate_clients(n_clients: int, rng: np.random.Generator) -> pd.DataFrame:
    client_id = np.arange(1, n_clients + 1)

    behavior_types = np.array(list(BEHAVIOR_PROFILES.keys()))
    behavior_probs = np.array([0.16, 0.15, 0.13, 0.15, 0.10, 0.12, 0.09, 0.10])
    latent_behavior_type = rng.choice(behavior_types, size=n_clients, p=behavior_probs)

    registration_date = random_dates(
        rng,
        pd.Timestamp("2018-01-01"),
        pd.Timestamp("2024-12-31"),
        n_clients,
    )

    age = np.clip(rng.normal(loc=40, scale=12, size=n_clients).round(), 20, 78).astype(int)
    birth_date = pd.Timestamp("2025-01-01") - pd.to_timedelta(age * 365 + rng.integers(0, 365, n_clients), unit="D")

    gender = rng.choice(["M", "F"], size=n_clients, p=[0.48, 0.52])

    regions = ["Almaty", "Astana", "Shymkent", "Karaganda", "Aktobe", "Atyrau", "East_KZ", "South_KZ", "North_KZ"]
    region = rng.choice(regions, size=n_clients, p=[0.25, 0.17, 0.12, 0.09, 0.08, 0.06, 0.08, 0.09, 0.06])

    city_type = rng.choice(
        ["large_city", "medium_city", "small_city", "rural"],
        size=n_clients,
        p=[0.42, 0.27, 0.20, 0.11],
    )

    income_group = rng.choice(
        ["low", "medium", "high", "premium"],
        size=n_clients,
        p=[0.28, 0.47, 0.20, 0.05],
    )

    employment_type = rng.choice(
        ["employee", "self_employed", "entrepreneur", "student", "retired", "unemployed"],
        size=n_clients,
        p=[0.53, 0.16, 0.10, 0.08, 0.08, 0.05],
    )

    customer_segment = []
    for inc, emp, beh in zip(income_group, employment_type, latent_behavior_type):
        if inc == "premium":
            customer_segment.append("premium")
        elif inc == "high" or beh == "high_value_busy":
            customer_segment.append("affluent")
        elif emp == "student" or beh == "young_mobile_first":
            customer_segment.append("youth")
        elif emp == "retired":
            customer_segment.append("pensioner")
        elif emp == "entrepreneur":
            customer_segment.append("sme_owner")
        else:
            customer_segment.append("mass")

    customer_segment = np.array(customer_segment)

    salary_project_flag = (
        (employment_type == "employee") & (rng.random(n_clients) < 0.62)
    ).astype(int)

    digital_adoption_level = []
    for beh in latent_behavior_type:
        if beh in ["loyal_digital", "young_mobile_first"]:
            digital_adoption_level.append(rng.choice(["high", "medium"], p=[0.80, 0.20]))
        elif beh in ["cash_user", "low_engagement"]:
            digital_adoption_level.append(rng.choice(["low", "medium"], p=[0.72, 0.28]))
        else:
            digital_adoption_level.append(rng.choice(["low", "medium", "high"], p=[0.20, 0.50, 0.30]))

    digital_adoption_level = np.array(digital_adoption_level)

    income_base = {
        "low": 160_000,
        "medium": 330_000,
        "high": 720_000,
        "premium": 1_450_000,
    }

    estimated_monthly_income = np.array([
        rng.lognormal(mean=np.log(income_base[g]), sigma=0.28)
        for g in income_group
    ]).round(2)

    churn_start_date = []
    for reg_date, beh in zip(registration_date, latent_behavior_type):
        p_churn = BEHAVIOR_PROFILES[beh]["churn_prob"]

        if rng.random() < p_churn:
            churn_date = random_dates(
                rng,
                max(pd.Timestamp("2024-03-01"), reg_date + pd.Timedelta(days=120)),
                pd.Timestamp("2025-09-30"),
                1,
            )[0]
            churn_start_date.append(churn_date)
        else:
            churn_start_date.append(pd.NaT)

    clients = pd.DataFrame(
        {
            "client_id": client_id,
            "registration_date": registration_date,
            "birth_date": birth_date,
            "gender": gender,
            "region": region,
            "city_type": city_type,
            "income_group": income_group,
            "employment_type": employment_type,
            "customer_segment": customer_segment,
            "salary_project_flag": salary_project_flag,
            "digital_adoption_level": digital_adoption_level,
            "estimated_monthly_income": estimated_monthly_income,
            "latent_behavior_type": latent_behavior_type,
            "churn_start_date": churn_start_date,
        }
    )

    return clients


def generate_products(clients: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    product_id = 1

    for row in clients.itertuples(index=False):
        product_types = ["debit_card"]

        if row.digital_adoption_level in ["medium", "high"] or rng.random() < 0.35:
            product_types.append("mobile_app")

        if row.salary_project_flag == 1 or rng.random() < 0.18:
            product_types.append("savings_account")

        if row.income_group in ["medium", "high", "premium"] and rng.random() < 0.30:
            product_types.append("credit_card")

        if row.income_group in ["high", "premium"] and rng.random() < 0.25:
            product_types.append("deposit")

        if rng.random() < 0.18:
            product_types.append("loan")

        if rng.random() < 0.35:
            product_types.append("transfer_service")

        product_types = list(dict.fromkeys(product_types))

        for product_type in product_types:
            open_start = max(pd.Timestamp(row.registration_date), START_DATE - pd.Timedelta(days=365))
            open_date = random_dates(rng, open_start, END_DATE, 1)[0]

            close_prob = 0.05
            if pd.notna(row.churn_start_date) and open_date < row.churn_start_date:
                close_prob = 0.18

            can_close_product = open_date + pd.Timedelta(days=30) <= END_DATE

            if can_close_product and rng.random() < close_prob:
                close_date = random_dates(
                    rng,
                    open_date + pd.Timedelta(days=30),
                    END_DATE,
                    1,
                )[0]
                status = "closed"
            else:
                close_date = pd.NaT
                status = "active"

            if product_type == "mobile_app":
                monthly_fee = 0
            elif product_type in ["debit_card", "credit_card"]:
                monthly_fee = float(rng.choice([0, 500, 900, 1500], p=[0.45, 0.25, 0.20, 0.10]))
            else:
                monthly_fee = float(rng.choice([0, 300, 700], p=[0.70, 0.20, 0.10]))

            rows.append(
                {
                    "product_id": product_id,
                    "client_id": row.client_id,
                    "product_type": product_type,
                    "open_date": open_date,
                    "close_date": close_date,
                    "status": status,
                    "monthly_fee": monthly_fee,
                }
            )
            product_id += 1

    return pd.DataFrame(rows)


def monthly_activity_multiplier(
    month: pd.Timestamp,
    registration_dates: np.ndarray,
    churn_dates: np.ndarray,
) -> np.ndarray:
    registered = registration_dates <= month_end(month)
    after_churn = pd.notna(churn_dates) & (churn_dates <= month)
    return np.where(registered, np.where(after_churn, 0.04, 1.0), 0.0)


def generate_transactions(clients: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    chunks = []

    client_ids = clients["client_id"].to_numpy()
    behavior = clients["latent_behavior_type"].to_numpy()
    registration_dates = clients["registration_date"].to_numpy(dtype="datetime64[ns]")
    churn_dates = clients["churn_start_date"].to_numpy(dtype="datetime64[ns]")
    income = clients["estimated_monthly_income"].to_numpy()

    base_rates = np.array([BEHAVIOR_PROFILES[b]["txn_rate"] for b in behavior])
    salary_flags = clients["salary_project_flag"].to_numpy()

    txn_types = np.array([
        "card_purchase",
        "cash_withdrawal",
        "p2p_transfer",
        "utility_payment",
        "mobile_topup",
        "salary_in",
        "deposit_in",
        "loan_payment",
        "fee",
    ])

    channels = np.array(["pos", "atm", "mobile_app", "internet_bank", "branch"])
    merchant_categories = np.array([
        "grocery",
        "transport",
        "pharmacy",
        "restaurant",
        "ecommerce",
        "utilities",
        "education",
        "travel",
        "cash",
        "other",
    ])

    transaction_id = 1

    for month in MONTHS:
        seasonal = 1.0 + 0.10 * np.sin((month.month - 1) / 12 * 2 * np.pi)
        multiplier = monthly_activity_multiplier(month, registration_dates, churn_dates)

        rate = base_rates * seasonal * multiplier
        counts = rng.poisson(rate)

        # Regular salary clients get an additional monthly salary transaction.
        salary_extra = ((salary_flags == 1) & (multiplier > 0) & (rng.random(len(clients)) < 0.88)).astype(int)
        counts = counts + salary_extra

        active_mask = counts > 0
        if not np.any(active_mask):
            continue

        ids = np.repeat(client_ids[active_mask], counts[active_mask])
        n = len(ids)

        day_offsets = rng.integers(0, month.days_in_month, size=n)
        dates = month + pd.to_timedelta(day_offsets, unit="D")

        txn_type = rng.choice(
            txn_types,
            size=n,
            p=[0.34, 0.12, 0.16, 0.12, 0.08, 0.07, 0.04, 0.04, 0.03],
        )

        channel = rng.choice(
            channels,
            size=n,
            p=[0.34, 0.15, 0.32, 0.12, 0.07],
        )

        merchant_category = rng.choice(
            merchant_categories,
            size=n,
            p=[0.24, 0.13, 0.08, 0.12, 0.12, 0.10, 0.04, 0.04, 0.07, 0.06],
        )

        income_lookup = pd.Series(income, index=client_ids).loc[ids].to_numpy()
        amount = rng.lognormal(mean=np.log(np.maximum(income_lookup * 0.045, 2_000)), sigma=0.75)

        salary_mask = txn_type == "salary_in"
        amount[salary_mask] = rng.normal(income_lookup[salary_mask], income_lookup[salary_mask] * 0.08).clip(30_000, None)

        fee_mask = txn_type == "fee"
        amount[fee_mask] = rng.choice([300, 500, 700, 1000, 1500], size=fee_mask.sum())

        is_successful = (rng.random(n) > 0.035).astype(int)

        chunk = pd.DataFrame(
            {
                "transaction_id": np.arange(transaction_id, transaction_id + n),
                "client_id": ids,
                "transaction_date": dates,
                "transaction_type": txn_type,
                "amount": amount.round(2),
                "channel": channel,
                "merchant_category": merchant_category,
                "is_successful": is_successful,
            }
        )
        transaction_id += n
        chunks.append(chunk)

    if not chunks:
        return pd.DataFrame()

    return pd.concat(chunks, ignore_index=True)


def generate_app_events(clients: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    chunks = []

    client_ids = clients["client_id"].to_numpy()
    behavior = clients["latent_behavior_type"].to_numpy()
    registration_dates = clients["registration_date"].to_numpy(dtype="datetime64[ns]")
    churn_dates = clients["churn_start_date"].to_numpy(dtype="datetime64[ns]")

    base_rates = np.array([BEHAVIOR_PROFILES[b]["app_rate"] for b in behavior])

    event_types = np.array([
        "login",
        "balance_view",
        "transaction_history_view",
        "transfer_created",
        "payment_created",
        "deposit_view",
        "loan_offer_view",
        "card_limit_view",
        "support_chat_opened",
    ])

    device_types = np.array(["ios", "android", "web"])

    event_id = 1
    session_id = 1

    for month in MONTHS:
        seasonal = 1.0 + 0.08 * np.cos((month.month - 1) / 12 * 2 * np.pi)
        multiplier = monthly_activity_multiplier(month, registration_dates, churn_dates)

        rate = base_rates * seasonal * multiplier
        counts = rng.poisson(rate)

        active_mask = counts > 0
        if not np.any(active_mask):
            continue

        ids = np.repeat(client_ids[active_mask], counts[active_mask])
        n = len(ids)

        day_offsets = rng.integers(0, month.days_in_month, size=n)
        dates = month + pd.to_timedelta(day_offsets, unit="D")

        event_type = rng.choice(
            event_types,
            size=n,
            p=[0.35, 0.20, 0.12, 0.09, 0.08, 0.04, 0.04, 0.04, 0.04],
        )

        device_type = rng.choice(device_types, size=n, p=[0.34, 0.58, 0.08])

        chunk = pd.DataFrame(
            {
                "event_id": np.arange(event_id, event_id + n),
                "client_id": ids,
                "event_date": dates,
                "event_type": event_type,
                "device_type": device_type,
                "session_id": np.arange(session_id, session_id + n),
            }
        )

        event_id += n
        session_id += n
        chunks.append(chunk)

    if not chunks:
        return pd.DataFrame()

    return pd.concat(chunks, ignore_index=True)


def generate_support_tickets(clients: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    rows = []

    ticket_types = np.array([
        "complaint",
        "card_issue",
        "app_issue",
        "loan_question",
        "deposit_question",
        "payment_issue",
        "general_question",
    ])

    statuses = np.array(["closed", "open", "escalated"])
    priorities = np.array(["low", "medium", "high", "critical"])

    ticket_id = 1

    for row in clients.itertuples(index=False):
        profile = BEHAVIOR_PROFILES[row.latent_behavior_type]
        annual_rate = profile["ticket_rate"] * 12
        count = rng.poisson(annual_rate * 2.2)

        if count <= 0:
            continue

        dates = random_dates(
            rng,
            max(pd.Timestamp(row.registration_date), START_DATE),
            END_DATE,
            count,
        )

        if row.latent_behavior_type == "complaint_prone":
            type_probs = [0.36, 0.14, 0.18, 0.07, 0.04, 0.12, 0.09]
            satisfaction_loc = 2.4
        else:
            type_probs = [0.10, 0.18, 0.14, 0.12, 0.08, 0.14, 0.24]
            satisfaction_loc = 4.0

        ticket_type = rng.choice(ticket_types, size=count, p=type_probs)
        status = rng.choice(statuses, size=count, p=[0.82, 0.12, 0.06])
        priority = rng.choice(priorities, size=count, p=[0.42, 0.38, 0.16, 0.04])
        satisfaction_score = np.clip(rng.normal(satisfaction_loc, 0.9, count).round(), 1, 5).astype(int)

        for i in range(count):
            rows.append(
                {
                    "ticket_id": ticket_id,
                    "client_id": row.client_id,
                    "ticket_date": dates[i],
                    "ticket_type": ticket_type[i],
                    "status": status[i],
                    "priority": priority[i],
                    "satisfaction_score": satisfaction_score[i],
                }
            )
            ticket_id += 1

    return pd.DataFrame(rows)


def generate_marketing_contacts(clients: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    chunks = []

    client_ids = clients["client_id"].to_numpy()
    behavior = clients["latent_behavior_type"].to_numpy()
    registration_dates = clients["registration_date"].to_numpy(dtype="datetime64[ns]")
    churn_dates = clients["churn_start_date"].to_numpy(dtype="datetime64[ns]")

    response_rate = np.array([BEHAVIOR_PROFILES[b]["marketing_response"] for b in behavior])
    contact_base_rate = np.where(np.isin(behavior, ["campaign_sensitive", "low_engagement"]), 0.75, 0.45)

    campaign_types = np.array(["retention", "cross_sell", "reactivation", "product_education", "cashback"])
    channels = np.array(["sms", "push", "email", "call"])
    offer_types = np.array(["cashback", "deposit_bonus", "free_transfer", "card_fee_discount", "loan_offer", "app_tutorial"])

    contact_id = 1

    for month in MONTHS:
        multiplier = monthly_activity_multiplier(month, registration_dates, churn_dates)
        counts = rng.poisson(contact_base_rate * np.where(multiplier > 0, 1.0, 0.2))

        active_mask = counts > 0
        if not np.any(active_mask):
            continue

        ids = np.repeat(client_ids[active_mask], counts[active_mask])
        n = len(ids)

        day_offsets = rng.integers(0, month.days_in_month, size=n)
        dates = month + pd.to_timedelta(day_offsets, unit="D")

        campaign_type = rng.choice(campaign_types, size=n, p=[0.18, 0.30, 0.14, 0.18, 0.20])
        channel = rng.choice(channels, size=n, p=[0.26, 0.44, 0.22, 0.08])
        offer_type = rng.choice(offer_types, size=n, p=[0.25, 0.13, 0.22, 0.14, 0.14, 0.12])

        rr_lookup = pd.Series(response_rate, index=client_ids).loc[ids].to_numpy()
        open_prob = np.clip(rr_lookup + 0.18, 0.02, 0.75)
        click_prob = np.clip(rr_lookup * 0.55, 0.01, 0.45)

        opened_flag = (rng.random(n) < open_prob).astype(int)
        clicked_flag = ((opened_flag == 1) & (rng.random(n) < click_prob)).astype(int)

        chunk = pd.DataFrame(
            {
                "contact_id": np.arange(contact_id, contact_id + n),
                "client_id": ids,
                "contact_date": dates,
                "campaign_type": campaign_type,
                "channel": channel,
                "offer_type": offer_type,
                "opened_flag": opened_flag,
                "clicked_flag": clicked_flag,
            }
        )

        contact_id += n
        chunks.append(chunk)

    if not chunks:
        return pd.DataFrame()

    return pd.concat(chunks, ignore_index=True)


def generate_customer_value_monthly(
    clients: pd.DataFrame,
    products: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    chunks = []

    product_counts = (
        products[products["status"] == "active"]
        .groupby("client_id")["product_id"]
        .count()
        .reindex(clients["client_id"])
        .fillna(0)
        .to_numpy()
    )

    client_ids = clients["client_id"].to_numpy()
    registration_dates = clients["registration_date"].to_numpy(dtype="datetime64[ns]")
    churn_dates = clients["churn_start_date"].to_numpy(dtype="datetime64[ns]")
    income = clients["estimated_monthly_income"].to_numpy()
    income_group = clients["income_group"].to_numpy()

    for month in MONTHS:
        multiplier = monthly_activity_multiplier(month, registration_dates, churn_dates)
        active_mask = multiplier > 0

        n = len(client_ids)

        revenue_base = income * 0.006 + product_counts * 600
        revenue = revenue_base * np.where(multiplier > 0.1, 1.0, 0.20) * rng.lognormal(0, 0.18, n)
        cost = 900 + product_counts * 160 + rng.normal(0, 120, n)
        cost = np.clip(cost, 100, None)
        net_value = revenue - cost

        balance_multiplier = np.select(
            [
                income_group == "low",
                income_group == "medium",
                income_group == "high",
                income_group == "premium",
            ],
            [0.7, 1.2, 2.3, 4.0],
            default=1.0,
        )

        balance_avg = income * balance_multiplier * rng.lognormal(0, 0.35, n)
        balance_avg = balance_avg * np.where(active_mask, 1.0, 0.45)

        chunk = pd.DataFrame(
            {
                "client_id": client_ids,
                "month": month,
                "estimated_revenue": revenue.round(2),
                "estimated_cost": cost.round(2),
                "net_value": net_value.round(2),
                "balance_avg": balance_avg.round(2),
            }
        )
        chunks.append(chunk)

    return pd.concat(chunks, ignore_index=True)


def generate_macro_calendar() -> pd.DataFrame:
    rows = []

    for month in MONTHS:
        is_holiday_season = int(month.month in [12, 1, 3])
        salary_payment_period = int(month.month in list(range(1, 13)))
        campaign_pressure_index = 1.0 + 0.15 * np.sin((month.month - 1) / 12 * 2 * np.pi)

        rows.append(
            {
                "month": month,
                "is_holiday_season": is_holiday_season,
                "salary_payment_period": salary_payment_period,
                "campaign_pressure_index": round(float(campaign_pressure_index), 4),
            }
        )

    return pd.DataFrame(rows)


def save_table(df: pd.DataFrame, output_dir: Path, filename: str) -> None:
    path = output_dir / filename
    df.to_csv(path, index=False)
    print(f"{filename}: {len(df):,} rows")


def generate_all(size: str, seed: int, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    n_clients = SIZE_CONFIG[size]

    print(f"Generating synthetic churn database: size={size}, clients={n_clients:,}, seed={seed}")
    print(f"Output directory: {output_dir.resolve()}")
    print()

    clients = generate_clients(n_clients, rng)
    products = generate_products(clients, rng)
    transactions = generate_transactions(clients, rng)
    app_events = generate_app_events(clients, rng)
    support_tickets = generate_support_tickets(clients, rng)
    marketing_contacts = generate_marketing_contacts(clients, rng)
    customer_value_monthly = generate_customer_value_monthly(clients, products, rng)
    macro_calendar = generate_macro_calendar()

    save_table(clients, output_dir, "clients.csv")
    save_table(products, output_dir, "products.csv")
    save_table(transactions, output_dir, "transactions.csv")
    save_table(app_events, output_dir, "app_events.csv")
    save_table(support_tickets, output_dir, "support_tickets.csv")
    save_table(marketing_contacts, output_dir, "marketing_contacts.csv")
    save_table(customer_value_monthly, output_dir, "customer_value_monthly.csv")
    save_table(macro_calendar, output_dir, "macro_calendar.csv")

    summary = pd.DataFrame(
        [
            {"metric": "clients", "value": len(clients)},
            {"metric": "products", "value": len(products)},
            {"metric": "transactions", "value": len(transactions)},
            {"metric": "app_events", "value": len(app_events)},
            {"metric": "support_tickets", "value": len(support_tickets)},
            {"metric": "marketing_contacts", "value": len(marketing_contacts)},
            {"metric": "customer_value_monthly", "value": len(customer_value_monthly)},
            {"metric": "macro_calendar", "value": len(macro_calendar)},
            {"metric": "synthetic_churn_clients_share", "value": clients["churn_start_date"].notna().mean()},
        ]
    )

    summary.to_csv(output_dir / "_generation_summary.csv", index=False)

    print()
    print(summary.to_string(index=False))
    print()
    print("Generation completed.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", choices=SIZE_CONFIG.keys(), default="small")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "data" / "raw" / "exports_small"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_all(
        size=args.size,
        seed=args.seed,
        output_dir=Path(args.output_dir),
    )


if __name__ == "__main__":
    main()