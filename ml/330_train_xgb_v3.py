#!/usr/bin/env python3

"""
Train the V3 XGBoost model.

V3 keeps the V2 feature set and adds early-care intervention flags
from medications/procedures, plus chronic diagnosis group indicators.

This is the no-demographic/no-administrative version used in the core report.
"""

import argparse

from xgb_train_common import train_from_split_view


CORE_NUMERIC_FEATURES = [
    "age_at_admit",
    "sodium_24h_first",
    "potassium_24h_first",
    "creatinine_24h_first",
    "lactate_24h_first",
    "charlson_min",
]


EXTENDED_LAB_FEATURES = [
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
    "antibiotic_24h",
    "insulin_24h",
    "diuretic_24h",
    "anticoag_antiplatelet_24h",
    "sedative_analgesic_24h",

    "airway_intubation_24h",
    "central_line_24h",
    "arterial_line_24h",
    "dialysis_24h",
    "chest_tube_24h",
]


CHRONIC_DX_FEATURES = [
    "copd",
    "chronic_liver",
    "malignancy",
    "cerebrovascular",
    "hypertension",
    "cad",
]


CATEGORICAL_FEATURES = []


DEFAULT_SPLIT_VIEW = "features.split_v3"
DEFAULT_OUT_DIR = "artifacts/xgb_v3_es_core"


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
        num_candidates=(
            CORE_NUMERIC_FEATURES
            + EXTENDED_LAB_FEATURES
            + LAB_MISSINGNESS_FEATURES
            + EARLY_CARE_FEATURES
            + CHRONIC_DX_FEATURES
        ),
        cat_candidates=CATEGORICAL_FEATURES,
        n_jobs=args.n_jobs,
    )


if __name__ == "__main__":
    main()