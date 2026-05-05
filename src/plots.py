from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import PrecisionRecallDisplay, RocCurveDisplay


def plot_roc_curve(y_true, y_score, output_path: Path, title: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 5))
    RocCurveDisplay.from_predictions(y_true, y_score, ax=ax)
    ax.plot([0, 1], [0, 1], linestyle="--")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(output_path, dpi=140)
    plt.close(fig)


def plot_pr_curve(y_true, y_score, output_path: Path, title: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 5))
    PrecisionRecallDisplay.from_predictions(y_true, y_score, ax=ax)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(output_path, dpi=140)
    plt.close(fig)


def plot_decile_churn(report, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(report["risk_decile"].astype(str), report["churn_rate"])
    ax.set_xlabel("Risk decile")
    ax.set_ylabel("Observed churn rate")
    ax.set_title("Observed churn rate by risk decile")
    fig.tight_layout()
    fig.savefig(output_path, dpi=140)
    plt.close(fig)


def plot_feature_importance(report, output_path: Path, top_n: int = 25) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = report.head(top_n).sort_values("importance", ascending=True)
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.barh(data["feature"], data["importance"])
    ax.set_xlabel("Importance")
    ax.set_ylabel("Feature")
    ax.set_title("Top feature importances")
    fig.tight_layout()
    fig.savefig(output_path, dpi=140)
    plt.close(fig)


def plot_psi_summary(report, output_path: Path, title: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = report.sort_values("psi", ascending=False).head(20).sort_values("psi", ascending=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(data["feature"], data["psi"])
    ax.set_xlabel("PSI")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(output_path, dpi=140)
    plt.close(fig)
