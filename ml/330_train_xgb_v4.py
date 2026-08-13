#!/usr/bin/env python3

"""
Train the V4 hospital-wide XGBoost model.

V4 keeps the V3 feature set and adds first/min/max vital-sign summaries
plus vital-sign missingness flags from the first 24 hours after admission.

This is the no-demographic/no-administrative version used in the core report.
"""

import argparse

from xgb_train_common import train_from_split_view


BASE_NUMERIC_FEATURES = [
    "age_at_admit",
    "charlson_min",

    "lactate_24h_first",
    "creatinine_24h_first",
    "bun_24h_first",
    "wbc_24h_first",
    "hemoglobin_24h_first",
    "platelets_24h_first",
    "bicarbonate_24h_first",

    "sodium_24h_first",
    "potassium_24h_first",
    "chloride_24h_first",
    "glucose_24h_first",
    "calcium_24h_first",
    "magnesium_24h_first",
    "phosphate_24h_first",
]


BASE_BINARY_FEATURES = [
    # lab missingness flags
    "lactate_24h_missing",
    "creatinine_24h_missing",
    "bun_24h_missing",
    "wbc_24h_missing",
    "hemoglobin_24h_missing",
    "platelets_24h_missing",
    "sodium_24h_missing",
    "potassium_24h_missing",
    "chloride_24h_missing",
    "glucose_24h_missing",
    "calcium_24h_missing",
    "magnesium_24h_missing",
    "phosphate_24h_missing",

    # medications in the first 24h
    "vasopressor_24h",
    "sedative_analgesic_24h",
    "antibiotic_24h",
    "insulin_24h",
    "diuretic_24h",
    "anticoag_antiplatelet_24h",

    # procedures in the first 24h
    "airway_intubation_24h",
    "arterial_line_24h",
    "dialysis_24h",
    "central_line_24h",
    "chest_tube_24h",

    # chronic diagnosis groups
    "malignancy",
    "chronic_liver",
    "cerebrovascular",
    "copd",
    "cad",
    "hypertension",
]


VITAL_NUMERIC_FEATURES = [
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


VITAL_BINARY_FEATURES = [
    "hr_24h_missing",
    "rr_24h_missing",
    "sbp_24h_missing",
    "dbp_24h_missing",
    "spo2_24h_missing",
    "temp_24h_missing",
]


NUMERIC_FEATURES = (
    BASE_NUMERIC_FEATURES
    + BASE_BINARY_FEATURES
    + VITAL_NUMERIC_FEATURES
    + VITAL_BINARY_FEATURES
)


CATEGORICAL_FEATURES = []


DEFAULT_SPLIT_VIEW = "features.split_v4"
DEFAULT_OUT_DIR = "artifacts/xgb_v4_nodemo"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split_view", default=DEFAULT_SPLIT_VIEW)
    parser.add_argument("--out_dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--label", default="y_inhosp_death")
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