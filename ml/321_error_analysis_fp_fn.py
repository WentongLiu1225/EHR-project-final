#!/usr/bin/env python3

"""
Perform FP/FN error analysis on validation predictions.

This script reads row-level validation predictions, assigns each case to
TP / FP / FN / TN, extracts high-risk false positives and all false negatives,
and summarizes numeric and binary features across error groups.

Generated row-level outputs should not be uploaded to GitHub.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def check_required_cols(df: pd.DataFrame, cols: list[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def add_error_group(
    df: pd.DataFrame,
    label_col: str,
    pred_col: str,
) -> pd.DataFrame:
    """
    Assign each row to TP, FP, FN, or TN based on true and predicted labels.
    """
    out = df.copy()

    y_true = pd.to_numeric(out[label_col], errors="coerce")
    y_pred = pd.to_numeric(out[pred_col], errors="coerce")

    conditions = [
        (y_true == 1) & (y_pred == 1),
        (y_true == 0) & (y_pred == 1),
        (y_true == 1) & (y_pred == 0),
        (y_true == 0) & (y_pred == 0),
    ]

    group_names = ["TP", "FP", "FN", "TN"]
    out["error_group"] = np.select(conditions, group_names, default="UNKNOWN")

    n_unknown = int((out["error_group"] == "UNKNOWN").sum())
    if n_unknown > 0:
        raise ValueError(
            f"Found {n_unknown} rows with UNKNOWN error group. "
            f"Check {label_col} and {pred_col}."
        )

    return out


def write_json(obj, path: Path) -> None:
    path.write_text(json.dumps(obj, indent=2, default=str))


def get_cohort_counts(
    df: pd.DataFrame,
    label_col: str,
    pred_col: str,
) -> dict:
    counts = (
        df["error_group"]
        .value_counts(dropna=False)
        .reindex(["TP", "FP", "FN", "TN"], fill_value=0)
        .to_dict()
    )

    out = {
        "n_total": int(len(df)),
        "label_prevalence": float(pd.to_numeric(df[label_col], errors="coerce").mean()),
        "pred_positive_rate_05": float(pd.to_numeric(df[pred_col], errors="coerce").mean()),
        "counts_by_group": {k: int(v) for k, v in counts.items()},
    }

    if "hadm_id" in df.columns:
        out["n_unique_hadm_id"] = int(df["hadm_id"].nunique())
        out["n_duplicate_hadm_rows"] = int(len(df) - df["hadm_id"].nunique())

    if "stay_id" in df.columns:
        out["n_unique_stay_id"] = int(df["stay_id"].nunique())

    return out


def summarize_numeric(
    df: pd.DataFrame,
    group_col: str,
    cols: list[str],
) -> pd.DataFrame:
    cols = [c for c in cols if c in df.columns]
    if not cols:
        return pd.DataFrame()

    rows = []

    for group in ["TP", "FP", "FN", "TN"]:
        sub = df[df[group_col] == group]
        if sub.empty:
            continue

        for col in cols:
            s = pd.to_numeric(sub[col], errors="coerce")
            has_data = s.notna().any()

            rows.append({
                "group": group,
                "feature": col,
                "n_nonmissing": int(s.notna().sum()),
                "missing_rate": float(s.isna().mean()),
                "mean": float(s.mean()) if has_data else np.nan,
                "median": float(s.median()) if has_data else np.nan,
                "p25": float(s.quantile(0.25)) if has_data else np.nan,
                "p75": float(s.quantile(0.75)) if has_data else np.nan,
            })

    return pd.DataFrame(rows)


def summarize_binary(
    df: pd.DataFrame,
    group_col: str,
    cols: list[str],
) -> pd.DataFrame:
    cols = [c for c in cols if c in df.columns]
    if not cols:
        return pd.DataFrame()

    rows = []

    for group in ["TP", "FP", "FN", "TN"]:
        sub = df[df[group_col] == group]
        if sub.empty:
            continue

        for col in cols:
            s = pd.to_numeric(sub[col], errors="coerce")
            has_data = s.notna().any()

            rows.append({
                "group": group,
                "feature": col,
                "n_nonmissing": int(s.notna().sum()),
                "missing_rate": float(s.isna().mean()),
                "rate_1": float(s.mean()) if has_data else np.nan,
                "count_1": int((s == 1).sum()),
            })

    return pd.DataFrame(rows)


def get_top_fp(
    df: pd.DataFrame,
    proba_col: str,
    top_n: int,
) -> pd.DataFrame:
    return (
        df[df["error_group"] == "FP"]
        .sort_values(proba_col, ascending=False)
        .head(top_n)
        .reset_index(drop=True)
        .copy()
    )


def get_all_fn(
    df: pd.DataFrame,
    proba_col: str,
) -> pd.DataFrame:
    return (
        df[df["error_group"] == "FN"]
        .sort_values(proba_col, ascending=False)
        .reset_index(drop=True)
        .copy()
    )


def get_candidate_numeric_cols() -> list[str]:
    return [
        "age_at_admit",
        "charlson_min",

        "lactate_24h_first",
        "creatinine_24h_first",
        "bun_24h_first",
        "wbc_24h_first",
        "hemoglobin_24h_first",
        "platelets_24h_first",
        "bicarbonate_24h_first",
        "chloride_24h_first",
        "calcium_24h_first",
        "glucose_24h_first",
        "sodium_24h_first",
        "potassium_24h_first",
        "magnesium_24h_first",
        "phosphate_24h_first",

        "hr_24h_first",
        "hr_24h_min",
        "hr_24h_max",
        "rr_24h_first",
        "rr_24h_min",
        "rr_24h_max",
        "sbp_24h_first",
        "sbp_24h_min",
        "sbp_24h_max",
        "dbp_24h_first",
        "dbp_24h_min",
        "dbp_24h_max",
        "spo2_24h_first",
        "spo2_24h_min",
        "spo2_24h_max",
        "temp_24h_first",
        "temp_24h_min",
        "temp_24h_max",
    ]


def get_candidate_binary_cols() -> list[str]:
    return [
        "lactate_24h_missing",
        "creatinine_24h_missing",
        "bun_24h_missing",
        "wbc_24h_missing",
        "hemoglobin_24h_missing",
        "platelets_24h_missing",
        "bicarbonate_24h_missing",
        "chloride_24h_missing",
        "calcium_24h_missing",
        "glucose_24h_missing",
        "sodium_24h_missing",
        "potassium_24h_missing",
        "magnesium_24h_missing",
        "phosphate_24h_missing",

        "hr_24h_missing",
        "rr_24h_missing",
        "sbp_24h_missing",
        "dbp_24h_missing",
        "spo2_24h_missing",
        "temp_24h_missing",

        "vasopressor_24h",
        "sedative_analgesic_24h",
        "antibiotic_24h",
        "insulin_24h",
        "diuretic_24h",
        "anticoag_antiplatelet_24h",

        "airway_intubation_24h",
        "arterial_line_24h",
        "dialysis_24h",
        "central_line_24h",
        "chest_tube_24h",

        "malignancy",
        "chronic_liver",
        "cerebrovascular",
        "copd",
        "cad",
        "hypertension",
    ]


def main(
    pred_csv: str,
    out_dir: str,
    label_col: str,
    pred_label_col: str,
    proba_col: str,
    fp_top_n: int,
):
    df = pd.read_csv(pred_csv)

    check_required_cols(df, [label_col, pred_label_col, proba_col])

    df = add_error_group(
        df,
        label_col=label_col,
        pred_col=pred_label_col,
    )

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    numeric_candidate_cols = get_candidate_numeric_cols()
    binary_candidate_cols = get_candidate_binary_cols()

    numeric_cols = [c for c in numeric_candidate_cols if c in df.columns]
    binary_cols = [c for c in binary_candidate_cols if c in df.columns]

    cohort_counts = get_cohort_counts(
        df,
        label_col=label_col,
        pred_col=pred_label_col,
    )

    cohort_counts_path = out_path / "cohort_counts.json"
    write_json(cohort_counts, cohort_counts_path)

    fp_top = get_top_fp(df, proba_col=proba_col, top_n=fp_top_n)
    fp_top_path = out_path / f"fp_top{fp_top_n}.csv"
    fp_top.to_csv(fp_top_path, index=False)

    fn_all = get_all_fn(df, proba_col=proba_col)
    fn_all_path = out_path / "fn_all.csv"
    fn_all.to_csv(fn_all_path, index=False)

    numeric_summary = summarize_numeric(
        df,
        group_col="error_group",
        cols=numeric_cols,
    )
    numeric_summary_path = out_path / "numeric_feature_summary_by_group.csv"
    numeric_summary.to_csv(numeric_summary_path, index=False)

    binary_summary = summarize_binary(
        df,
        group_col="error_group",
        cols=binary_cols,
    )
    binary_summary_path = out_path / "binary_feature_rates_by_group.csv"
    binary_summary.to_csv(binary_summary_path, index=False)

    output_summary = {
        "pred_csv": pred_csv,
        "out_dir": str(out_path),
        "saved": {
            "cohort_counts_json": str(cohort_counts_path),
            "fp_top_csv": str(fp_top_path),
            "fn_all_csv": str(fn_all_path),
            "numeric_summary_csv": str(numeric_summary_path),
            "binary_summary_csv": str(binary_summary_path),
        },
        "features_summarized": {
            "numeric": numeric_cols,
            "binary": binary_cols,
        },
        "counts_by_group": cohort_counts["counts_by_group"],
        "n_total": cohort_counts["n_total"],
        "label_prevalence": cohort_counts["label_prevalence"],
        "pred_positive_rate_05": cohort_counts["pred_positive_rate_05"],
    }

    if "n_unique_hadm_id" in cohort_counts:
        output_summary["n_unique_hadm_id"] = cohort_counts["n_unique_hadm_id"]
        output_summary["n_duplicate_hadm_rows"] = cohort_counts["n_duplicate_hadm_rows"]

    if "n_unique_stay_id" in cohort_counts:
        output_summary["n_unique_stay_id"] = cohort_counts["n_unique_stay_id"]

    print(json.dumps(output_summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pred_csv",
        required=True,
        help="Path to valid_predictions_detailed.csv",
    )
    parser.add_argument(
        "--out_dir",
        required=True,
        help="Directory to save error-analysis outputs",
    )
    parser.add_argument("--label_col", default="y_inhosp_death")
    parser.add_argument("--pred_label_col", default="y_pred_label_05")
    parser.add_argument("--proba_col", default="y_pred_proba")
    parser.add_argument("--fp_top_n", type=int, default=200)

    args = parser.parse_args()

    main(
        pred_csv=args.pred_csv,
        out_dir=args.out_dir,
        label_col=args.label_col,
        pred_label_col=args.pred_label_col,
        proba_col=args.proba_col,
        fp_top_n=args.fp_top_n,
    )