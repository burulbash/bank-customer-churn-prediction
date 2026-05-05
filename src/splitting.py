from __future__ import annotations

import pandas as pd

from .config import DATE_COL, TARGET, TRAIN_END_DATE, VALID_END_DATE
from .utils import validate_columns


def make_time_split(
    df: pd.DataFrame,
    date_col: str = DATE_COL,
    train_end_date: str = TRAIN_END_DATE,
    valid_end_date: str = VALID_END_DATE,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    validate_columns(df.columns, [date_col, TARGET])

    data = df.copy()
    data[date_col] = pd.to_datetime(data[date_col], errors="coerce")
    data = data.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)

    train = data[data[date_col] < pd.Timestamp(train_end_date)].copy()
    valid = data[(data[date_col] >= pd.Timestamp(train_end_date)) & (data[date_col] < pd.Timestamp(valid_end_date))].copy()
    test = data[data[date_col] >= pd.Timestamp(valid_end_date)].copy()

    if min(len(train), len(valid), len(test)) == 0:
        raise ValueError(
            "One of the time-based splits is empty. Check snapshot_date range "
            f"and split dates: train_end={train_end_date}, valid_end={valid_end_date}."
        )

    return train, valid, test


def split_summary(train: pd.DataFrame, valid: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split_name, split_df in [("train", train), ("valid", valid), ("test", test)]:
        rows.append(
            {
                "split": split_name,
                "rows": len(split_df),
                "min_snapshot_date": split_df[DATE_COL].min(),
                "max_snapshot_date": split_df[DATE_COL].max(),
                "churn_rate": split_df[TARGET].mean(),
            }
        )
    return pd.DataFrame(rows)
