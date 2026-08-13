#!/usr/bin/env python3

"""
Train the V6 non-ICU XGBoost model.

V6 uses non-ICU hospital admissions and includes age, first-24h labs,
lab missingness indicators, early-care intervention flags, and chronic
diagnosis group indicators.

This is the no-demographic/no-administrative version used in the core report.
"""

import argparse

from xgb_train_common import train_from_split_view


DEFAULT_SPLIT_VIEW = "features.split_v6_nonicu"
DEFAULT_OUT_DIR = "artifacts/xgb_v6_nonicu_core"
LABEL = "y_inhosp_death"


BASE_NUMERIC_FEATURES = [
    "age_at_admit",
    "charlson_min",
]


LAB_NUMERIC_FEATURES = [
    "sodium_24h_first",
    "potassium_24h_first",
    "creatinine_24h_first",
    "lactate_24h_first",
    "glucose_24h_first",
    "bun_24h_first",
    "chloride_24h_first",
    "bicarbonate_24h_first",
    "calcium_24h_first",
    "magnesium_24h_first",
    "phosphate_24h_first",
    "wbc_24h_first",
    "hemoglobin_24h_first",
    "platelets_24h_first",
]


LAB_MISSINGNESS_FEATURES = [
    "sodium_24h_missing",
    "potassium_24h_missing",
    "creatinine_24h_missing",
    "lactate_24h_missing",
    "glucose_24h_missing",
    "bun_24h_missing",
    "chloride_24h_missing",
    "bicarbonate_24h_missing",
    "calcium_24h_missing",
    "magnesium_24h_missing",
    "phosphate_24h_missing",
    "wbc_24h_missing",
    "hemoglobin_24h_missing",
    "platelets_24h_missing",
]


EARLY_CARE_FEATURES = [
    "vasopressor_24h",
    "sedative_analgesic_24h",
    "antibiotic_24h",
    "airway_intubation_24h",
    "arterial_line_24h",
    "dialysis_24h",
    "central_line_24h",
    "chest_tube_24h",
]


CHRONIC_DX_FEATURES = [
    "malignancy",
    "chronic_liver",
    "cerebrovascular",
    "copd",
    "cad",
    "hypertension",
]


NUMERIC_FEATURES = (
    BASE_NUMERIC_FEATURES
    + LAB_NUMERIC_FEATURES
    + LAB_MISSINGNESS_FEATURES
    + EARLY_CARE_FEATURES
    + CHRONIC_DX_FEATURES
)


CATEGORICAL_FEATURES = []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split_view", default=DEFAULT_SPLIT_VIEW)
    parser.add_argument("--out_dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--label", default=LABEL)
    parser.add_argument("--n_jobs", type=int, default=4)

    args = parser.parse_args()

    train_from_split_view(
        split_view=args.split_view,
        label=args.label,
        out_dir=args.out_dir,
        num_candidates=NUMERIC_FEATURES,
        cat_candidates=CATEGORICAL_FEATURES,
        split_col="split",
        n_jobs=args.n_jobs,
    )


if __name__ == "__main__":
    main()