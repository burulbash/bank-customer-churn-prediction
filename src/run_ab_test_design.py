from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import REPORTS_DIR  # noqa: E402
from src.utils import ensure_artifact_dirs, safe_write_csv  # noqa: E402


def main() -> None:
    ensure_artifact_dirs()
    segments_path = REPORTS_DIR / "business_actions_report.csv"
    if not segments_path.exists():
        raise FileNotFoundError("Run src/run_segmentation.py first.")

    segments = pd.read_csv(segments_path)
    eligible = segments[segments["business_segment"] != "standard_monitoring"].copy()

    rows = []
    for row in eligible.itertuples(index=False):
        customers = int(row.customers)
        treatment = customers // 2
        control = customers - treatment
        rows.append(
            {
                "business_segment": row.business_segment,
                "recommended_action": row.recommended_action,
                "eligible_customers": customers,
                "control_group_size": control,
                "treatment_group_size": treatment,
                "randomization_unit": "client_id",
                "stratification": "business_segment + risk/value profile",
                "primary_metric": "60-day retention rate",
                "secondary_metrics": "transaction_count_60d, app_login_count_60d, net_value_60d",
                "guardrail_metrics": "complaint_rate, unsubscribe_rate, support_ticket_rate",
            }
        )

    design = pd.DataFrame(rows)
    safe_write_csv(design, REPORTS_DIR / "ab_test_design.csv")
    print(design)


if __name__ == "__main__":
    main()
