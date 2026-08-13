#!/usr/bin/env python3

"""
Train the V4 logistic regression model.

V4 keeps the V3 feature set and adds first/min/max vital-sign summaries
plus vital-sign missingness flags from the first 24 hours after admission.

This is the no-demographic/no-administrative version used for the core report.
"""

from train_logit_common import train_eval_save


FEATURES_VIEW = "features.inhosp_mortality_features_v4"
SPLIT_VIEW = "features.split_v4"
OUT_DIR = "artifacts/logit_v4_nodemo"
LABEL = "y_inhosp_death"


CONTINUOUS_FEATURES = [
    # V3 continuous features
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

    # V4 vital-sign summaries
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

    # vital-sign missingness flags
    "hr_24h_missing",
    "rr_24h_missing",
    "sbp_24h_missing",
    "dbp_24h_missing",
    "spo2_24h_missing",
    "temp_24h_missing",

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