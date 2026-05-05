from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DEFAULT_POSTGRES_TABLE, DEFAULT_SAMPLE_PATH, REPORTS_DIR, PLOTS_DIR, TARGET  # noqa: E402
from src.db import read_dataset_from_postgres  # noqa: E402
from src.plots import plot_psi_summary  # noqa: E402
from src.psi import calculate_psi, psi_status  # noqa: E402
from src.splitting import make_time_split, split_summary  # noqa: E402
from src.utils import ensure_artifact_dirs, safe_write_csv  # noqa: E402

DEFAULT_PSI_FEATURES = [
    "days_since_last_txn",
    "days_since_last_app_login",
    "txn_count_90d",
    "app_login_count_90d",
    "active_products_count",
    "complaints_count_90d",
    "avg_satisfaction_score_90d",
    "customer_segment",
    "value_segment",
    "activity_segment",
]


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


def build_psi_report(df: pd.DataFrame, predictions_path: Path | None, make_plots: bool = False) -> None:
    train, valid, test = make_time_split(df)
    safe_write_csv(split_summary(train, valid, test), REPORTS_DIR / "monitoring_split_summary.csv")

    summary_rows = []
    details = []

    for comparison_name, actual_df in [("train_vs_valid", valid), ("train_vs_test", test)]:
        for feature in DEFAULT_PSI_FEATURES:
            if feature not in train.columns:
                continue
            psi_value, detail = calculate_psi(train[feature], actual_df[feature], feature, comparison_name)
            details.append(detail)
            summary_rows.append(
                {
                    "comparison": comparison_name,
                    "feature": feature,
                    "psi": psi_value,
                    "status": psi_status(psi_value),
                }
            )

    if predictions_path and predictions_path.exists():
        preds = pd.read_csv(predictions_path)
        score_cols = [c for c in preds.columns if c.startswith("score_") and c != "score_dummy_prior"]
        if score_cols:
            score_col = score_cols[0]
            merged = df[["client_id", "snapshot_date"]].merge(
                preds[["client_id", "snapshot_date", score_col]],
                on=["client_id", "snapshot_date"],
                how="left",
            )
            df_with_score = df.copy()
            df_with_score["churn_score"] = merged[score_col]
            scored = df_with_score.dropna(subset=["churn_score"])
            # In the default training flow only the test set predictions are saved.
            # Score PSI is computed only when predictions are available for all time splits.
            try:
                train_s, valid_s, test_s = make_time_split(scored)
            except ValueError:
                train_s = valid_s = test_s = None

            if train_s is not None:
                for comparison_name, actual_df in [("score_train_vs_valid", valid_s), ("score_train_vs_test", test_s)]:
                    psi_value, detail = calculate_psi(train_s["churn_score"], actual_df["churn_score"], "churn_score", comparison_name)
                    details.append(detail)
                    summary_rows.append(
                        {
                            "comparison": comparison_name,
                            "feature": "churn_score",
                            "psi": psi_value,
                            "status": psi_status(psi_value),
                        }
                    )

    summary = pd.DataFrame(summary_rows).sort_values(["comparison", "psi"], ascending=[True, False])
    detail_df = pd.concat(details, ignore_index=True) if details else pd.DataFrame()

    safe_write_csv(summary, REPORTS_DIR / "psi_feature_summary.csv")
    safe_write_csv(detail_df, REPORTS_DIR / "psi_feature_details.csv")

    if make_plots:
        for comparison in summary["comparison"].unique():
            sub = summary[summary["comparison"] == comparison]
            plot_psi_summary(sub, PLOTS_DIR / f"psi_{comparison}.png", f"PSI - {comparison}")

    print(summary)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["csv", "postgres"], default="csv")
    parser.add_argument("--csv-path", default=str(DEFAULT_SAMPLE_PATH))
    parser.add_argument("--predictions-path", default=str(REPORTS_DIR / "test_predictions.csv"))
    parser.add_argument("--db-host", default="localhost")
    parser.add_argument("--db-port", default="5432")
    parser.add_argument("--db-name", default="bank_churn_db")
    parser.add_argument("--db-user", default="postgres")
    parser.add_argument("--db-password", default=None)
    parser.add_argument("--table-name", default=DEFAULT_POSTGRES_TABLE)
    parser.add_argument("--make-plots", action="store_true", help="Generate PSI plots.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_artifact_dirs()
    df = read_dataset(args)
    build_psi_report(df, Path(args.predictions_path), make_plots=args.make_plots)


if __name__ == "__main__":
    main()
