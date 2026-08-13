#!/usr/bin/env python3

"""
Train the V3 logistic regression model.

V3 keeps the V2 feature set and adds early treatment/intervention signals
from medications and procedures, plus broader chronic diagnosis groups.
"""

from train_logit_common import train_eval_save


FEATURES_VIEW = "features.inhosp_mortality_features_v3"
SPLIT_VIEW = "features.split_v3"
OUT_DIR = "artifacts/logit_v3_core"
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
    "antibiotic_24h",
    "insulin_24h",
    "diuretic_24h",
    "anticoag_antiplatelet_24h",
    "sedative_analgesic_24h",

    # procedures in the first 24h
    "airway_intubation_24h",
    "central_line_24h",
    "arterial_line_24h",
    "dialysis_24h",
    "chest_tube_24h",

    # chronic diagnosis groups
    "copd",
    "chronic_liver",
    "malignancy",
    "cerebrovascular",
    "hypertension",
    "cad",
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
    )


if __name__ == "__main__":
    main()