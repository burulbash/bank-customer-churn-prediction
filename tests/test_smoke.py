from pathlib import Path

import pandas as pd

from src.config import DEFAULT_SAMPLE_PATH, TARGET, DATE_COL
from src.splitting import make_time_split
from src.metrics import classification_metrics


def test_sample_dataset_exists_and_has_target():
    assert Path(DEFAULT_SAMPLE_PATH).exists()
    df = pd.read_csv(DEFAULT_SAMPLE_PATH)
    assert TARGET in df.columns
    assert DATE_COL in df.columns
    assert df[TARGET].isin([0, 1]).all()


def test_time_split_non_empty():
    df = pd.read_csv(DEFAULT_SAMPLE_PATH)
    train, valid, test = make_time_split(df)
    assert len(train) > 0
    assert len(valid) > 0
    assert len(test) > 0


def test_metrics_smoke():
    df = pd.read_csv(DEFAULT_SAMPLE_PATH).head(100)
    y_true = df[TARGET].to_numpy()
    y_score = [df[TARGET].mean()] * len(df)
    result = classification_metrics(y_true, y_score)
    assert "roc_auc" in result
    assert "lift_at_10" in result
