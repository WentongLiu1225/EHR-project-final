#!/usr/bin/env python3

"""
Train the V1 XGBoost model.

V1 uses a small baseline feature set:
- age at admission
- first available core labs within 24 hours of admission
- minimal Charlson-style comorbidity summary

This is the no-demographic/no-administrative version used in the core report.
"""

import argparse

from xgb_train_common import train_from_split_view


V1_NUMERIC_FEATURES = [
    "age_at_admit",
    "sodium_24h_first",
    "potassium_24h_first",
    "creatinine_24h_first",
    "lactate_24h_first",
    "charlson_min",
]


CATEGORICAL_FEATURES = []


DEFAULT_SPLIT_VIEW = "features.split"
DEFAULT_OUT_DIR = "artifacts/xgb_v1_es_core"


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
        num_candidates=V1_NUMERIC_FEATURES,
        cat_candidates=CATEGORICAL_FEATURES,
        n_jobs=args.n_jobs,
    )


if __name__ == "__main__":
    main()