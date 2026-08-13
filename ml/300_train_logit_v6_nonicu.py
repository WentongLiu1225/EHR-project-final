#!/usr/bin/env python3

"""
Train the V6 non-ICU logistic regression model.

V6 uses the non-ICU admission-level feature table based on V3 features,
excluding hospital admissions with any linked ICU stay. This model uses no
demographic or administrative variables.
"""

from train_logit_common import train_eval_save


FEATURES_VIEW = "features.inhosp_mortality_features_v6_nonicu"
SPLIT_VIEW = "features.split_v6_nonicu"
OUT_DIR = "artifacts/logit_v6_nonicu_core"
LABEL = "y_inhosp_death"


CONTINUOUS_FEATURES = [
    "age_at_admit",

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

    "charlson_min",
]


BINARY_FEATURES = [
    # lab missingness flags
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

    # medications in the first 24h
    "vasopressor_24h",
    "sedative_analgesic_24h",
    "antibiotic_24h",

    # procedure flags from the V3 feature set
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


CATEGORICAL_FEATURES = []


def main():
    train_eval_save(
        features_view=FEATURES_VIEW,
        split_view=SPLIT_VIEW,
        out_dir=OUT_DIR,
        label=LABEL,
        continuous_candidates=CONTINUOUS_FEATURES,
        binary_candidates=BINARY_FEATURES,
        categorical_candidates=CATEGORICAL_FEATURES,
        drop_all_missing_train=True,
        check_preprocessed_nan=True,
        save_latest=True,
    )


if __name__ == "__main__":
    main()