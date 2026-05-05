from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"
PLOTS_DIR = PROJECT_ROOT / "outputs" / "plots"


def ensure_dirs() -> None:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def save_bar(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    xlabel: str,
    ylabel: str,
    output_name: str,
    horizontal: bool = False,
) -> None:
    data = df.copy()

    plt.figure(figsize=(9, 5))

    if horizontal:
        plt.barh(data[x_col].astype(str), data[y_col])
        plt.xlabel(ylabel)
        plt.ylabel(xlabel)
    else:
        plt.bar(data[x_col].astype(str), data[y_col])
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.xticks(rotation=30, ha="right")

    plt.title(title)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / output_name, dpi=140)
    plt.close()


def plot_model_comparison() -> None:
    path = REPORTS_DIR / "model_metrics.csv"
    if not path.exists():
        return

    df = pd.read_csv(path)
    test_df = df[df["split"] == "test"].copy()

    if test_df.empty:
        return

    test_df = test_df.sort_values("roc_auc", ascending=False)

    save_bar(
        test_df,
        x_col="model",
        y_col="roc_auc",
        title="Test ROC-AUC by model",
        xlabel="Model",
        ylabel="ROC-AUC",
        output_name="model_comparison_test_roc_auc.png",
    )

    save_bar(
        test_df,
        x_col="model",
        y_col="lift_at_10",
        title="Test Lift@Top10% by model",
        xlabel="Model",
        ylabel="Lift@Top10%",
        output_name="model_comparison_test_lift_at_10.png",
    )


def plot_decile_report() -> None:
    path = REPORTS_DIR / "churn_decile_report.csv"
    if not path.exists():
        return

    df = pd.read_csv(path)

    decile_col = None
    for candidate in ["decile", "risk_decile", "score_decile"]:
        if candidate in df.columns:
            decile_col = candidate
            break

    churn_col = None
    for candidate in ["actual_churn_rate", "churn_rate", "target_rate"]:
        if candidate in df.columns:
            churn_col = candidate
            break

    if decile_col is None or churn_col is None:
        return

    df = df.sort_values(decile_col)

    save_bar(
        df,
        x_col=decile_col,
        y_col=churn_col,
        title="Actual churn rate by risk decile",
        xlabel="Risk decile",
        ylabel="Actual churn rate",
        output_name="churn_rate_by_risk_decile.png",
    )


def plot_risk_segments() -> None:
    path = REPORTS_DIR / "risk_segment_report.csv"
    if not path.exists():
        return

    df = pd.read_csv(path)

    if "risk_segment" not in df.columns or "actual_churn_rate" not in df.columns:
        return

    order = ["very_low", "low", "medium", "high", "very_high"]
    df["risk_segment"] = pd.Categorical(df["risk_segment"], categories=order, ordered=True)
    df = df.sort_values("risk_segment")

    save_bar(
        df,
        x_col="risk_segment",
        y_col="actual_churn_rate",
        title="Actual churn rate by risk segment",
        xlabel="Risk segment",
        ylabel="Actual churn rate",
        output_name="churn_rate_by_risk_segment.png",
    )


def plot_feature_importance() -> None:
    candidates = [
        REPORTS_DIR / "feature_importance_logistic_regression.csv",
        REPORTS_DIR / "feature_importance_random_forest.csv",
    ]

    for path in candidates:
        if not path.exists():
            continue

        df = pd.read_csv(path)

        if "feature" not in df.columns or "importance" not in df.columns:
            continue

        data = (
            df.sort_values("importance", ascending=False)
            .head(20)
            .sort_values("importance", ascending=True)
        )

        output_name = path.stem + "_top20.png"

        save_bar(
            data,
            x_col="feature",
            y_col="importance",
            title=f"Top 20 features - {path.stem.replace('feature_importance_', '')}",
            xlabel="Feature",
            ylabel="Importance",
            output_name=output_name,
            horizontal=True,
        )


def plot_psi_summary() -> None:
    path = REPORTS_DIR / "psi_feature_summary.csv"
    if not path.exists():
        return

    df = pd.read_csv(path)

    if not {"comparison", "feature", "psi"}.issubset(df.columns):
        return

    for comparison in df["comparison"].dropna().unique():
        data = (
            df[df["comparison"] == comparison]
            .sort_values("psi", ascending=False)
            .head(15)
            .sort_values("psi", ascending=True)
        )

        save_bar(
            data,
            x_col="feature",
            y_col="psi",
            title=f"Top PSI features - {comparison}",
            xlabel="Feature",
            ylabel="PSI",
            output_name=f"top_psi_features_{comparison}.png",
            horizontal=True,
        )


def plot_threshold_report() -> None:
    path = REPORTS_DIR / "threshold_report.csv"
    if not path.exists():
        return

    df = pd.read_csv(path)

    if "threshold" not in df.columns:
        return

    metric_cols = [c for c in ["precision", "recall", "f1"] if c in df.columns]

    if not metric_cols:
        return

    plt.figure(figsize=(8, 5))

    for col in metric_cols:
        plt.plot(df["threshold"], df[col], marker="o", label=col)

    plt.xlabel("Threshold")
    plt.ylabel("Metric value")
    plt.title("Threshold tuning")
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "threshold_tuning.png", dpi=140)
    plt.close()


def main() -> None:
    ensure_dirs()

    plot_model_comparison()
    plot_decile_report()
    plot_risk_segments()
    plot_feature_importance()
    plot_psi_summary()
    plot_threshold_report()

    print("Generated plots:")
    for path in sorted(PLOTS_DIR.glob("*.png")):
        print(path)


if __name__ == "__main__":
    main()
