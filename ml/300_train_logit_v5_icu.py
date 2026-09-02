#!/usr/bin/env python3

"""
Train the V5 ICU-only logistic regression model.

V5 uses the ICU-only admission-level feature table, keeping one row per hospital
admission based on the first ICU stay. The model uses no demographic or
administrative variables.
"""

from train_logit_common import train_eval_save


FEATURES_VIEW = "features.inhosp_mortality_features_v5_icu"
SPLIT_VIEW = "features.split_v5_icu"
OUT_DIR = "artifacts/logit_v5_icu_nodemo"
LABEL = "y_inhosp_death"


NUMERIC_FEATURES = [
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

    "vasopressor_24h",
    "sedative_analgesic_24h",
    "antibiotic_24h",
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

    "hr_24h_missing",
    "rr_24h_missing",
    "sbp_24h_missing",
    "dbp_24h_missing",
    "spo2_24h_missing",
    "temp_24h_missing",
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
        save_latest=True,
    )


if __name__ == "__main__":
    main()