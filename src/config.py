from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_SAMPLE_DIR = PROJECT_ROOT / "data" / "sample"
REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"
PLOTS_DIR = PROJECT_ROOT / "outputs" / "plots"
MODELS_DIR = PROJECT_ROOT / "outputs" / "models"

TARGET = "target_churn_60d"
DATE_COL = "snapshot_date"
ID_COLS = ["client_id", "snapshot_date"]

DEFAULT_SAMPLE_PATH = DATA_SAMPLE_DIR / "churn_feature_table_sample.csv"
DEFAULT_POSTGRES_TABLE = "mart.churn_feature_table"

TRAIN_END_DATE = "2025-01-01"
VALID_END_DATE = "2025-07-01"

RANDOM_STATE = 42

ARTIFACT_DIRS = [REPORTS_DIR, PLOTS_DIR, MODELS_DIR]

CATEGORICAL_FEATURES = [
    "gender",
    "region",
    "city_type",
    "income_group",
    "employment_type",
    "customer_segment",
    "digital_adoption_level",
    "value_segment",
    "activity_segment",
    "complaint_segment",
    "digital_segment",
]

# Helper columns are useful for validation and business analysis, but they are not allowed
# as model features because they are either identifiers or use the future target window.
NON_FEATURE_COLUMNS = [
    "client_id",
    "snapshot_date",
    "target_churn_60d",
    "future_txn_count_60d",
    "future_app_login_count_60d",
    "future_product_open_count_60d",
]

MODEL_PARAMS = {
    "logistic_regression": {
        "max_iter": 1000,
    },
    "random_forest": {
        "n_estimators": 40,
        "max_depth": 8,
        "min_samples_leaf": 50,
        "n_jobs": 1,
        "random_state": RANDOM_STATE,
    },
    "xgboost": {
        "n_estimators": 160,
        "max_depth": 4,
        "learning_rate": 0.05,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "eval_metric": "logloss",
        "tree_method": "hist",
        "random_state": RANDOM_STATE,
        "n_jobs": 1,
    },
    "catboost": {
        "iterations": 160,
        "depth": 5,
        "learning_rate": 0.05,
        "loss_function": "Logloss",
        "eval_metric": "AUC",
        "random_seed": RANDOM_STATE,
        "verbose": False,
    },
}

RISK_SEGMENT_LABELS = ["very_low", "low", "medium", "high", "very_high"]
