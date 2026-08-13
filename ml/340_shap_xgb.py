#!/usr/bin/env python3

"""
Run SHAP explainability analysis for a trained XGBoost pipeline.

This script loads a saved XGBoost sklearn pipeline, reads validation data from
a PostgreSQL split view, applies the fitted preprocessing step, computes SHAP
contribution values using XGBoost's native pred_contribs method, and saves
feature importance rankings and SHAP plots.
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from joblib import load
from sqlalchemy import create_engine


def make_engine():
    pg_host = os.getenv("PGHOST", "localhost")
    pg_port = os.getenv("PGPORT", "5432")
    pg_db = os.getenv("PGDATABASE", "mimic")
    pg_user = os.getenv("PGUSER", "mimicuser")
    pg_password = os.getenv("PGPASSWORD", "")

    return create_engine(
        f"postgresql+psycopg2://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
    )


def read_view(engine, view_name: str) -> pd.DataFrame:
    raw = engine.raw_connection()
    try:
        return pd.read_sql_query(f"select * from {view_name}", raw)
    finally:
        raw.close()


def latest_model_path(model_dir: str) -> Path:
    model_dir_path = Path(model_dir)

    latest_path = model_dir_path / "model_latest.joblib"
    if latest_path.exists():
        return latest_path

    joblibs = sorted(model_dir_path.glob("model_*.joblib"))
    if not joblibs:
        raise FileNotFoundError(f"No model joblib found in {model_dir}")

    return joblibs[-1]


def get_column_transformer_cols(pre, name: str) -> list[str]:
    for transformer_name, _transformer, cols in pre.transformers_:
        if transformer_name == name:
            return list(cols) if cols is not None else []

    return []


def get_pipeline_feature_cols(pipe, df: pd.DataFrame) -> list[str]:
    """
    Extract raw feature columns used by the fitted pipeline.
    """
    pre = pipe.named_steps["pre"]

    cols = []
    cols += get_column_transformer_cols(pre, "num")
    cols += get_column_transformer_cols(pre, "cont")
    cols += get_column_transformer_cols(pre, "bin")
    cols += get_column_transformer_cols(pre, "cat")

    cols = list(dict.fromkeys([c for c in cols if c in df.columns]))

    if not cols:
        raise ValueError("No pipeline feature columns found in dataframe.")

    return cols


def transformed_feature_names(pre, Xt) -> list[str]:
    """
    Return transformed feature names aligned with the preprocessed matrix columns.
    """
    if hasattr(pre, "get_feature_names_out"):
        names = list(pre.get_feature_names_out())
    else:
        names = [f"f{i}" for i in range(Xt.shape[1])]

    if len(names) != Xt.shape[1]:
        raise ValueError(
            f"Feature-name mismatch after preprocessing: "
            f"{len(names)} names vs {Xt.shape[1]} columns."
        )

    return names


def latest_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def main(
    model_dir: str,
    split_view: str,
    label: str,
    out_dir: Optional[str],
    sample_n: int,
    random_state: int,
):
    engine = make_engine()
    df = read_view(engine, split_view)

    if "split" not in df.columns:
        raise ValueError("split_view must contain column `split`.")

    if label not in df.columns:
        raise ValueError(f"label `{label}` not found in {split_view}.")

    valid = df[df["split"] == "valid"].copy()
    if valid.empty:
        raise ValueError("No validation rows found in split_view.")

    model_path = latest_model_path(model_dir)
    pipe = load(model_path)

    raw_feature_cols = get_pipeline_feature_cols(pipe, valid)
    X = valid[raw_feature_cols].copy()

    if sample_n is not None and len(X) > sample_n:
        X = X.sample(n=sample_n, random_state=random_state)

    pre = pipe.named_steps["pre"]
    clf = pipe.named_steps["xgb"]

    Xt = pre.transform(X)

    if hasattr(Xt, "toarray"):
        Xt_dense = Xt.toarray()
    else:
        Xt_dense = Xt

    feature_names = transformed_feature_names(pre, Xt_dense)

    booster = clf.get_booster()

    dmatrix = xgb.DMatrix(
        Xt_dense,
        feature_names=feature_names,
    )

    contrib = booster.predict(dmatrix, pred_contribs=True)

    # XGBoost returns one extra column for the bias term.
    shap_values = contrib[:, :-1]

    mean_abs = np.abs(shap_values).mean(axis=0)
    ranking_df = (
        pd.DataFrame({
            "feature": feature_names,
            "mean_abs_shap": mean_abs,
        })
        .sort_values("mean_abs_shap", ascending=False)
        .reset_index(drop=True)
    )

    if out_dir is None:
        out_path = Path(model_dir) / "shap"
    else:
        out_path = Path(out_dir)

    out_path.mkdir(parents=True, exist_ok=True)
    stamp = latest_stamp()

    ranking_csv = out_path / "shap_mean_abs_ranking.csv"
    ranking_df.to_csv(ranking_csv, index=False)

    beeswarm_path = out_path / "beeswarm_top20.png"
    plt.figure()
    shap.summary_plot(
        shap_values,
        Xt_dense,
        feature_names=feature_names,
        max_display=20,
        show=False,
    )
    plt.tight_layout()
    plt.savefig(beeswarm_path, dpi=200, bbox_inches="tight")
    plt.close()

    bar_path = out_path / "bar_top20.png"
    plt.figure()
    shap.summary_plot(
        shap_values,
        Xt_dense,
        feature_names=feature_names,
        plot_type="bar",
        max_display=20,
        show=False,
    )
    plt.tight_layout()
    plt.savefig(bar_path, dpi=200, bbox_inches="tight")
    plt.close()

    report_path = out_path / f"shap_report_{stamp}.json"

    report = {
        "model_dir": model_dir,
        "model_path": str(model_path),
        "split_view": split_view,
        "label": label,
        "n_sampled": int(X.shape[0]),
        "n_raw_features": int(len(raw_feature_cols)),
        "n_transformed_features": int(len(feature_names)),
        "top5": ranking_df.head(5).to_dict(orient="records"),
        "saved_report": str(report_path),
        "ranking_csv": str(ranking_csv),
        "beeswarm": str(beeswarm_path),
        "bar": str(bar_path),
    }

    report_path.write_text(json.dumps(report, indent=2))

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_dir", required=True)
    parser.add_argument("--split_view", required=True)
    parser.add_argument("--label", default="y_inhosp_death")
    parser.add_argument("--out_dir", default=None)
    parser.add_argument("--sample_n", type=int, default=2000)
    parser.add_argument("--random_state", type=int, default=42)

    args = parser.parse_args()

    main(
        model_dir=args.model_dir,
        split_view=args.split_view,
        label=args.label,
        out_dir=args.out_dir,
        sample_n=args.sample_n,
        random_state=args.random_state,
    )
    