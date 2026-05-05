from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def recall_at_k(y_true: np.ndarray, y_score: np.ndarray, top_fraction: float) -> float:
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score).astype(float)
    n_top = max(1, int(np.ceil(len(y_true) * top_fraction)))
    top_idx = np.argsort(y_score)[::-1][:n_top]
    positives = y_true.sum()
    if positives == 0:
        return float("nan")
    return float(y_true[top_idx].sum() / positives)


def lift_at_k(y_true: np.ndarray, y_score: np.ndarray, top_fraction: float) -> float:
    y_true = np.asarray(y_true).astype(int)
    base_rate = y_true.mean()
    if base_rate == 0:
        return float("nan")
    n_top = max(1, int(np.ceil(len(y_true) * top_fraction)))
    top_idx = np.argsort(y_score)[::-1][:n_top]
    return float(y_true[top_idx].mean() / base_rate)


def classification_metrics(
    y_true: np.ndarray,
    y_score: np.ndarray,
    threshold: float = 0.5,
) -> dict[str, float]:
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score).astype(float)
    y_pred = (y_score >= threshold).astype(int)

    if len(np.unique(y_true)) < 2:
        roc_auc = float("nan")
        pr_auc = float("nan")
    else:
        roc_auc = float(roc_auc_score(y_true, y_score))
        pr_auc = float(average_precision_score(y_true, y_score))

    return {
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "recall_at_10": recall_at_k(y_true, y_score, 0.10),
        "recall_at_20": recall_at_k(y_true, y_score, 0.20),
        "lift_at_10": lift_at_k(y_true, y_score, 0.10),
        "lift_at_20": lift_at_k(y_true, y_score, 0.20),
        "base_churn_rate": float(y_true.mean()),
        "mean_score": float(y_score.mean()),
    }


def threshold_report(y_true: np.ndarray, y_score: np.ndarray, thresholds: list[float]) -> pd.DataFrame:
    rows = []
    for threshold in thresholds:
        y_pred = (np.asarray(y_score) >= threshold).astype(int)
        selected_share = float(y_pred.mean())
        rows.append(
            {
                "threshold": threshold,
                "selected_share": selected_share,
                "precision": float(precision_score(y_true, y_pred, zero_division=0)),
                "recall": float(recall_score(y_true, y_pred, zero_division=0)),
                "f1": float(f1_score(y_true, y_pred, zero_division=0)),
            }
        )
    return pd.DataFrame(rows)


def decile_report(y_true: np.ndarray, y_score: np.ndarray) -> pd.DataFrame:
    data = pd.DataFrame({"target": y_true, "score": y_score}).sort_values("score", ascending=False)
    data["risk_decile"] = pd.qcut(
        data["score"].rank(method="first"),
        q=10,
        labels=[f"D{i}" for i in range(1, 11)],
    )
    data["risk_decile"] = data["risk_decile"].cat.reorder_categories([f"D{i}" for i in range(10, 0, -1)], ordered=True)

    total_churners = data["target"].sum()
    report = (
        data.groupby("risk_decile", observed=True)
        .agg(
            customers=("target", "size"),
            churners=("target", "sum"),
            churn_rate=("target", "mean"),
            min_score=("score", "min"),
            max_score=("score", "max"),
            avg_score=("score", "mean"),
        )
        .reset_index()
        .sort_values("risk_decile", ascending=True)
    )
    report["churners_captured_share"] = report["churners"] / max(total_churners, 1)
    report["lift"] = report["churn_rate"] / max(data["target"].mean(), 1e-12)
    return report


def confusion_matrix_report(y_true: np.ndarray, y_score: np.ndarray, threshold: float) -> pd.DataFrame:
    y_pred = (np.asarray(y_score) >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return pd.DataFrame([
        {"threshold": threshold, "tn": tn, "fp": fp, "fn": fn, "tp": tp}
    ])
