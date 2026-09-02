#!/usr/bin/env python3

"""
Inspect coefficients from a trained logistic regression pipeline.

This script loads a saved model, rebuilds the feature names after preprocessing,
saves the coefficients and odds ratios to CSV, and prints the largest
coefficients by absolute value.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import load


def latest_model_path(model_dir: str) -> Path:
    model_dir_path = Path(model_dir)

    latest_path = model_dir_path / "model_latest.joblib"
    if latest_path.exists():
        return latest_path

    models = sorted(model_dir_path.glob("model_*.joblib"))
    if not models:
        raise FileNotFoundError(f"No model_*.joblib found under {model_dir}")

    return models[-1]


def get_transformer_cols(pre, name: str):
    for transformer_name, _transformer, cols in pre.transformers_:
        if transformer_name == name:
            return list(cols) if not isinstance(cols, slice) else cols

    return None


def main(model_dir: str, top: int, out_csv: str | None):
    model_path = latest_model_path(model_dir)
    pipe = load(model_path)

    pre = pipe.named_steps.get("pre")
    clf = pipe.named_steps.get("clf")

    if pre is None or clf is None:
        raise ValueError("Pipeline must have named steps: 'pre' and 'clf'.")

    feature_names = []
    feature_types = []

    cont_cols = get_transformer_cols(pre, "cont") or get_transformer_cols(pre, "num")
    if cont_cols and not isinstance(cont_cols, slice):
        feature_names += list(cont_cols)
        feature_types += ["cont"] * len(cont_cols)

    bin_cols = get_transformer_cols(pre, "bin")
    if bin_cols and not isinstance(bin_cols, slice):
        feature_names += list(bin_cols)
        feature_types += ["bin"] * len(bin_cols)

    cat_cols = get_transformer_cols(pre, "cat")
    if cat_cols and not isinstance(cat_cols, slice):
        cat_pipe = pre.named_transformers_.get("cat")

        if cat_pipe is None:
            raise ValueError("Found 'cat' columns but no 'cat' transformer.")

        if "oh" not in cat_pipe.named_steps:
            raise ValueError("Expected OneHotEncoder step named 'oh' inside the 'cat' pipeline.")

        oh = cat_pipe.named_steps["oh"]
        cat_ohe_names = list(oh.get_feature_names_out(cat_cols))

        feature_names += cat_ohe_names
        feature_types += ["cat"] * len(cat_ohe_names)

    if not feature_names:
        raise ValueError("No feature names extracted. Check the ColumnTransformer names.")

    if not hasattr(clf, "coef_"):
        raise TypeError("This inspector only works for linear models with coef_.")

    coef = clf.coef_.ravel()
    intercept = float(np.ravel(clf.intercept_)[0]) if hasattr(clf, "intercept_") else float("nan")

    if len(feature_names) != len(coef):
        raise ValueError(
            f"feature_names ({len(feature_names)}) != coef ({len(coef)}). "
            "This usually means feature names were reconstructed incorrectly."
        )

    coef_df = pd.DataFrame({
        "feature": feature_names,
        "type": feature_types,
        "coef": coef,
        "odds_ratio": np.exp(coef),
        "abs_coef": np.abs(coef),
    }).sort_values("abs_coef", ascending=False)

    if out_csv is None:
        out_csv_path = Path(model_dir) / "coeffs_latest.csv"
    else:
        out_csv_path = Path(out_csv)

    coef_df.to_csv(out_csv_path, index=False)

    summary = {
        "model_dir": model_dir,
        "model_path": str(model_path),
        "intercept": intercept,
        "n_total_features": int(len(coef_df)),
        "top": int(top),
        "top_features": coef_df.head(top)[
            ["feature", "type", "coef", "odds_ratio"]
        ].to_dict(orient="records"),
        "saved_csv": str(out_csv_path),
        "notes": [
            "coef is in log-odds units; odds_ratio = exp(coef).",
            "Continuous variables are interpreted after median imputation and standardization.",
            "Binary variables compare 1 vs 0 after missing-value imputation.",
        ],
    }

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_dir",
        required=True,
        help="Artifact directory containing model_*.joblib or model_latest.joblib",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=30,
        help="Number of top absolute-coefficient features to print",
    )
    parser.add_argument(
        "--out_csv",
        default=None,
        help="Optional output CSV path; default: <model_dir>/coeffs_latest.csv",
    )

    args = parser.parse_args()

    main(
        model_dir=args.model_dir,
        top=args.top,
        out_csv=args.out_csv,
    )