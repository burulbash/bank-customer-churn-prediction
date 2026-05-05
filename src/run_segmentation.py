from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DATE_COL, DEFAULT_POSTGRES_TABLE, DEFAULT_SAMPLE_PATH, REPORTS_DIR, RISK_SEGMENT_LABELS, TARGET  # noqa: E402
from src.db import read_dataset_from_postgres  # noqa: E402
from src.utils import ensure_artifact_dirs, safe_write_csv, validate_columns  # noqa: E402


def read_dataset(args: argparse.Namespace) -> pd.DataFrame:
    if args.source == "csv":
        return pd.read_csv(args.csv_path)
    return read_dataset_from_postgres(
        db_name=args.db_name,
        db_user=args.db_user,
        db_password=args.db_password,
        db_host=args.db_host,
        db_port=args.db_port,
        table_name=args.table_name,
    )


def choose_score_column(predictions: pd.DataFrame, preferred_model: str | None) -> str:
    if preferred_model:
        col = f"score_{preferred_model}"
        if col in predictions.columns:
            return col
    score_cols = [col for col in predictions.columns if col.startswith("score_") and col != "score_dummy_prior"]
    if not score_cols:
        raise ValueError("No model score columns found in test_predictions.csv")
    return score_cols[0]


def assign_risk_segments(scores: pd.Series) -> pd.Series:
    return pd.qcut(scores.rank(method="first"), q=5, labels=RISK_SEGMENT_LABELS)


def recommended_action(row: pd.Series) -> str:
    if row["business_segment"] == "high_value_high_risk":
        return "Personal manager call with tailored retention offer"
    if row["business_segment"] == "complaint_driven_churn":
        return "Service recovery and priority support follow-up"
    if row["business_segment"] == "digital_drop_off":
        return "Push campaign with cashback for app activity"
    if row["business_segment"] == "low_product_engagement":
        return "Automated cross-sell / product education campaign"
    if row["business_segment"] == "low_value_high_risk":
        return "Low-cost automated SMS or push retention campaign"
    return "No immediate retention action"


def assign_business_segment(df: pd.DataFrame) -> pd.Series:
    value_high = df.get("value_segment", "").isin(["high_value", "premium_value"])
    high_risk = df["risk_segment"].isin(["high", "very_high"])
    low_value = df.get("value_segment", "").eq("low_value")

    complaint = (df.get("complaints_count_90d", 0) > 0) | (df.get("avg_satisfaction_score_90d", 5).fillna(5) <= 2)
    digital_drop = (df.get("app_login_change_pct_30d", 0) < -0.5) | (df.get("days_since_last_app_login", 0).fillna(0) > 45)
    low_product = df.get("active_products_count", 0) <= 1

    result = pd.Series("standard_monitoring", index=df.index)
    result[high_risk & low_value] = "low_value_high_risk"
    result[high_risk & low_product] = "low_product_engagement"
    result[high_risk & digital_drop] = "digital_drop_off"
    result[high_risk & complaint] = "complaint_driven_churn"
    result[high_risk & value_high] = "high_value_high_risk"
    return result


def build_reports(dataset: pd.DataFrame, predictions: pd.DataFrame, score_col: str) -> None:
    validate_columns(dataset.columns, ["client_id", DATE_COL, TARGET])
    validate_columns(predictions.columns, ["client_id", DATE_COL, TARGET, score_col])

    dataset[DATE_COL] = pd.to_datetime(dataset[DATE_COL], errors="coerce")
    predictions[DATE_COL] = pd.to_datetime(predictions[DATE_COL], errors="coerce")

    analysis_cols = [
        "client_id",
        DATE_COL,
        TARGET,
        "customer_segment",
        "value_segment",
        "activity_segment",
        "digital_segment",
        "complaint_segment",
        "estimated_monthly_income",
        "net_value_3m",
        "active_products_count",
        "txn_count_90d",
        "app_login_count_90d",
        "complaints_count_90d",
        "avg_satisfaction_score_90d",
        "app_login_change_pct_30d",
        "days_since_last_app_login",
    ]
    analysis_cols = [col for col in analysis_cols if col in dataset.columns]

    df = predictions[["client_id", DATE_COL, TARGET, score_col]].merge(
        dataset[analysis_cols].drop_duplicates(["client_id", DATE_COL]),
        on=["client_id", DATE_COL, TARGET],
        how="left",
    )

    df = df.rename(columns={score_col: "churn_score"})
    df["risk_segment"] = assign_risk_segments(df["churn_score"])
    df["business_segment"] = assign_business_segment(df)
    df["recommended_action"] = df.apply(recommended_action, axis=1)

    risk_report = (
        df.groupby("risk_segment", observed=True)
        .agg(
            customers=("client_id", "size"),
            actual_churn_rate=(TARGET, "mean"),
            avg_churn_score=("churn_score", "mean"),
            avg_estimated_income=("estimated_monthly_income", "mean"),
            avg_net_value_3m=("net_value_3m", "mean"),
            avg_active_products_count=("active_products_count", "mean"),
            avg_txn_count_90d=("txn_count_90d", "mean"),
            avg_app_login_count_90d=("app_login_count_90d", "mean"),
            complaint_rate=("complaints_count_90d", lambda x: (x.fillna(0) > 0).mean()),
        )
        .reset_index()
    )

    business_report = (
        df.groupby(["business_segment", "recommended_action"], observed=True)
        .agg(
            customers=("client_id", "size"),
            actual_churn_rate=(TARGET, "mean"),
            avg_churn_score=("churn_score", "mean"),
            avg_net_value_3m=("net_value_3m", "mean"),
        )
        .reset_index()
        .sort_values(["actual_churn_rate", "customers"], ascending=[False, False])
    )

    safe_write_csv(df, REPORTS_DIR / "customer_level_churn_segments.csv")
    safe_write_csv(risk_report, REPORTS_DIR / "risk_segment_report.csv")
    safe_write_csv(business_report, REPORTS_DIR / "business_actions_report.csv")

    print("Risk segment report")
    print(risk_report)
    print("\nBusiness actions report")
    print(business_report)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["csv", "postgres"], default="csv")
    parser.add_argument("--csv-path", default=str(DEFAULT_SAMPLE_PATH))
    parser.add_argument("--predictions-path", default=str(REPORTS_DIR / "test_predictions.csv"))
    parser.add_argument("--preferred-model", default=None)
    parser.add_argument("--db-host", default="localhost")
    parser.add_argument("--db-port", default="5432")
    parser.add_argument("--db-name", default="bank_churn_db")
    parser.add_argument("--db-user", default="postgres")
    parser.add_argument("--db-password", default=None)
    parser.add_argument("--table-name", default=DEFAULT_POSTGRES_TABLE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_artifact_dirs()

    predictions = pd.read_csv(args.predictions_path)
    score_col = choose_score_column(predictions, args.preferred_model)
    dataset = read_dataset(args)
    build_reports(dataset, predictions, score_col)


if __name__ == "__main__":
    main()
