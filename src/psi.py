from __future__ import annotations

import numpy as np
import pandas as pd


def psi_status(value: float) -> str:
    if value < 0.10:
        return "stable"
    if value < 0.25:
        return "moderate_shift"
    return "significant_shift"


def _bin_series(expected: pd.Series, actual: pd.Series, n_bins: int = 10) -> tuple[pd.Series, pd.Series]:
    if pd.api.types.is_numeric_dtype(expected):
        exp = pd.to_numeric(expected, errors="coerce")
        act = pd.to_numeric(actual, errors="coerce")
        non_missing = exp.dropna()
        if non_missing.nunique() <= 2:
            return exp.astype("Int64").astype(str).replace("<NA>", "MISSING"), act.astype("Int64").astype(str).replace("<NA>", "MISSING")
        edges = np.unique(non_missing.quantile(np.linspace(0, 1, n_bins + 1)).to_numpy())
        if len(edges) < 3:
            return exp.astype("Int64").astype(str).replace("<NA>", "MISSING"), act.astype("Int64").astype(str).replace("<NA>", "MISSING")
        edges[0] = -np.inf
        edges[-1] = np.inf
        exp_bin = pd.cut(exp, bins=edges, include_lowest=True).astype(str).where(~exp.isna(), "MISSING")
        act_bin = pd.cut(act, bins=edges, include_lowest=True).astype(str).where(~act.isna(), "MISSING")
        return exp_bin, act_bin

    exp = expected.astype("object").where(~expected.isna(), "MISSING").astype(str)
    act = actual.astype("object").where(~actual.isna(), "MISSING").astype(str)
    top_categories = exp.value_counts(normalize=True)
    top_categories = top_categories[top_categories >= 0.01].index.tolist()
    return exp.where(exp.isin(top_categories), "OTHER"), act.where(act.isin(top_categories), "OTHER")


def calculate_psi(expected: pd.Series, actual: pd.Series, feature: str, comparison: str) -> tuple[float, pd.DataFrame]:
    exp_bin, act_bin = _bin_series(expected, actual)
    exp_dist = exp_bin.value_counts(normalize=True, dropna=False)
    act_dist = act_bin.value_counts(normalize=True, dropna=False)
    all_bins = sorted(set(exp_dist.index).union(act_dist.index))
    eps = 1e-6
    rows = []
    total = 0.0
    for bin_name in all_bins:
        exp_pct = float(exp_dist.get(bin_name, 0.0))
        act_pct = float(act_dist.get(bin_name, 0.0))
        exp_adj = max(exp_pct, eps)
        act_adj = max(act_pct, eps)
        component = (act_adj - exp_adj) * np.log(act_adj / exp_adj)
        total += component
        rows.append({
            "comparison": comparison,
            "feature": feature,
            "bin": bin_name,
            "expected_pct": exp_pct,
            "actual_pct": act_pct,
            "psi_component": component,
        })
    return total, pd.DataFrame(rows)
