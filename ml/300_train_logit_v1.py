#!/usr/bin/env python3

"""
Train the V1 logistic regression model.

V1 uses a small core feature set:
- age at admission
- first-within-24h core labs
- minimal Charlson-style comorbidity summary
"""

from train_logit_common import train_eval_save


FEATURES_VIEW = "features.inhosp_mortality_features"
SPLIT_VIEW = "features.split"
OUT_DIR = "artifacts/logit_v1_core"
LABEL = "y_inhosp_death"


NUMERIC_FEATURES = [
    "age_at_admit",
    "sodium_24h_first",
    "potassium_24h_first",
    "creatinine_24h_first",
    "lactate_24h_first",
    "charlson_min",
]

BINARY_FEATURES = []

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