from __future__ import annotations

import argparse
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (  # noqa: E402
    CATEGORICAL_FEATURES,
    DATE_COL,
    DEFAULT_POSTGRES_TABLE,
    DEFAULT_SAMPLE_PATH,
    MODEL_PARAMS,
    MODELS_DIR,
    NON_FEATURE_COLUMNS,
    PLOTS_DIR,
    RANDOM_STATE,
    REPORTS_DIR,
    TARGET,
)
from src.db import read_dataset_from_postgres  # noqa: E402
from src.metrics import (  # noqa: E402
    classification_metrics,
    confusion_matrix_report,
    decile_report,
    threshold_report,
)
from src.plots import plot_decile_churn, plot_feature_importance, plot_pr_curve, plot_roc_curve  # noqa: E402
from src.splitting import make_time_split, split_summary  # noqa: E402
from src.utils import ensure_artifact_dirs, safe_write_csv, validate_columns  # noqa: E402

MODEL_DIR = MODELS_DIR / "churn"


def make_one_hot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", min_frequency=20, sparse_output=True)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", min_frequency=20, sparse=True)


def read_dataset(args: argparse.Namespace) -> pd.DataFrame:
    if args.source == "csv":
        path = Path(args.csv_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")
        df = pd.read_csv(path)
    else:
        df = read_dataset_from_postgres(
            db_name=args.db_name,
            db_user=args.db_user,
            db_password=args.db_password,
            db_host=args.db_host,
            db_port=args.db_port,
            table_name=args.table_name,
        )

    validate_columns(df.columns, [TARGET, DATE_COL])
    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
    df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce").astype(int)
    return df


def get_feature_columns(df: pd.DataFrame) -> tuple[list[str], list[str], list[str]]:
    excluded = set(NON_FEATURE_COLUMNS)
    features = [col for col in df.columns if col not in excluded]

    categorical = [col for col in CATEGORICAL_FEATURES if col in features]
    numeric = [col for col in features if col not in categorical and pd.api.types.is_numeric_dtype(df[col])]

    # Keep only explicitly typed categorical or numeric columns. Date-like/object helper columns are excluded.
    feature_columns = numeric + categorical

    safe_write_csv(pd.DataFrame({"feature": feature_columns}), REPORTS_DIR / "feature_columns.csv")
    safe_write_csv(
        pd.DataFrame(
            {
                "feature": numeric + categorical,
                "feature_type": ["numeric"] * len(numeric) + ["categorical"] * len(categorical),
            }
        ),
        REPORTS_DIR / "feature_types.csv",
    )
    return feature_columns, numeric, categorical


def build_preprocessor(numeric_features: list[str], categorical_features: list[str]) -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", make_one_hot_encoder()),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_features),
            ("cat", categorical_pipeline, categorical_features),
        ],
        remainder="drop",
    )


def get_models(y_train: pd.Series, include_heavy_models: bool = False) -> dict[str, object]:
    models: dict[str, object] = {
        "dummy_prior": DummyClassifier(strategy="prior"),
        "logistic_regression": LogisticRegression(
            **MODEL_PARAMS["logistic_regression"],
            class_weight=None,
            solver="liblinear",
            random_state=RANDOM_STATE,
        ),
        "random_forest": RandomForestClassifier(**MODEL_PARAMS["random_forest"]),
    }

    if include_heavy_models:
        try:
            from xgboost import XGBClassifier
            models["xgboost"] = XGBClassifier(**MODEL_PARAMS["xgboost"])
        except ImportError:
            print("xgboost is not installed; skipping XGBoost model.")

        try:
            from catboost import CatBoostClassifier
            models["catboost"] = CatBoostClassifier(**MODEL_PARAMS["catboost"])
        except ImportError:
            print("catboost is not installed; skipping CatBoost model.")

    return models


def save_feature_importance(model_name: str, pipeline: Pipeline) -> None:
    preprocessor = pipeline.named_steps["preprocess"]
    estimator = pipeline.named_steps["model"]

    if not hasattr(preprocessor, "get_feature_names_out"):
        return

    feature_names = preprocessor.get_feature_names_out()

    if hasattr(estimator, "feature_importances_"):
        values = estimator.feature_importances_
    elif hasattr(estimator, "get_feature_importance"):
        values = estimator.get_feature_importance()
    elif hasattr(estimator, "coef_"):
        values = np.abs(estimator.coef_).ravel()
    else:
        return

    report = (
        pd.DataFrame({"feature": feature_names, "importance": values})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )
    safe_write_csv(report, REPORTS_DIR / f"feature_importance_{model_name}.csv")


def train_and_evaluate(df: pd.DataFrame, include_heavy_models: bool = False, make_plots: bool = False) -> None:
    ensure_artifact_dirs()
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    train_df, valid_df, test_df = make_time_split(df)
    safe_write_csv(split_summary(train_df, valid_df, test_df), REPORTS_DIR / "time_split_summary.csv")

    feature_cols, numeric_features, categorical_features = get_feature_columns(train_df)
    preprocessor = build_preprocessor(numeric_features, categorical_features)

    datasets = {
        "train": (train_df[feature_cols], train_df[TARGET].astype(int)),
        "valid": (valid_df[feature_cols], valid_df[TARGET].astype(int)),
        "test": (test_df[feature_cols], test_df[TARGET].astype(int)),
    }

    X_train, y_train = datasets["train"]
    models = get_models(y_train, include_heavy_models=include_heavy_models)

    metric_rows = []
    test_predictions = test_df[["client_id", DATE_COL, TARGET]].copy()

    best_model_name = None
    best_valid_auc = -np.inf

    for model_name, estimator in models.items():
        print(f"Training {model_name}...")
        pipeline = Pipeline(steps=[("preprocess", preprocessor), ("model", estimator)])
        pipeline.fit(X_train, y_train)

        for split_name, (X_split, y_split) in datasets.items():
            y_score = pipeline.predict_proba(X_split)[:, 1]
            metrics = classification_metrics(y_split.to_numpy(), y_score)
            metric_rows.append({"model": model_name, "split": split_name, "rows": len(y_split), **metrics})

            if split_name == "valid" and metrics["roc_auc"] > best_valid_auc:
                best_valid_auc = metrics["roc_auc"]
                best_model_name = model_name

            if split_name == "test":
                test_predictions[f"score_{model_name}"] = y_score
                if make_plots:
                    plot_roc_curve(y_split, y_score, PLOTS_DIR / f"roc_{model_name}_test.png", f"ROC - {model_name} - test")
                    plot_pr_curve(y_split, y_score, PLOTS_DIR / f"pr_{model_name}_test.png", f"PR - {model_name} - test")

        save_feature_importance(model_name, pipeline)
        joblib.dump(pipeline, MODEL_DIR / f"{model_name}.joblib")

    metrics_df = pd.DataFrame(metric_rows).sort_values(["split", "roc_auc"], ascending=[True, False])
    safe_write_csv(metrics_df, REPORTS_DIR / "model_metrics.csv")
    safe_write_csv(test_predictions, REPORTS_DIR / "test_predictions.csv")

    if best_model_name is None:
        raise RuntimeError("Could not select a best model.")

    score_col = f"score_{best_model_name}"
    y_test = test_predictions[TARGET].astype(int).to_numpy()
    y_score = test_predictions[score_col].to_numpy()

    deciles = decile_report(y_test, y_score)
    thresholds = threshold_report(y_test, y_score, thresholds=[0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50])
    confusion = confusion_matrix_report(y_test, y_score, threshold=0.20)

    safe_write_csv(deciles, REPORTS_DIR / "churn_decile_report.csv")
    safe_write_csv(thresholds, REPORTS_DIR / "threshold_report.csv")
    safe_write_csv(confusion, REPORTS_DIR / "confusion_matrix_best_model.csv")
    if make_plots:
        plot_decile_churn(deciles, PLOTS_DIR / "churn_rate_by_decile_test.png")

    safe_write_csv(pd.DataFrame([{"best_model": best_model_name, "selection_metric": "valid_roc_auc", "valid_roc_auc": best_valid_auc}]), REPORTS_DIR / "best_model_summary.csv")

    print("\nBest model:", best_model_name)
    print(metrics_df)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["csv", "postgres"], default="csv")
    parser.add_argument("--csv-path", default=str(DEFAULT_SAMPLE_PATH))
    parser.add_argument("--db-host", default="localhost")
    parser.add_argument("--db-port", default="5432")
    parser.add_argument("--db-name", default="bank_churn_db")
    parser.add_argument("--db-user", default="postgres")
    parser.add_argument("--db-password", default=None)
    parser.add_argument("--table-name", default=DEFAULT_POSTGRES_TABLE)
    parser.add_argument("--include-heavy-models", action="store_true", help="Also train optional XGBoost/CatBoost models.")
    parser.add_argument("--make-plots", action="store_true", help="Generate ROC/PR/decile plots.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = read_dataset(args)
    train_and_evaluate(df, include_heavy_models=args.include_heavy_models, make_plots=args.make_plots)


if __name__ == "__main__":
    main()
