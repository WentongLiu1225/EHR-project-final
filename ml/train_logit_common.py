#!/usr/bin/env python3

"""
Common logistic regression training utilities for the in-hospital mortality project.

This module loads feature data from PostgreSQL, attaches train/valid split labels,
builds a preprocessing + logistic regression pipeline, evaluates AUROC/AUPRC,
and saves timestamped model and metric outputs.

Optional arguments support the V6 non-ICU model, where some columns may be
entirely missing in the training set.
"""

import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import dump
from sqlalchemy import create_engine

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def make_engine():
    pg_host = os.getenv("PGHOST", "localhost")
    pg_port = os.getenv("PGPORT", "5432")
    pg_db = os.getenv("PGDATABASE", "mimic")
    pg_user = os.getenv("PGUSER", "mimicuser")
    pg_password = os.getenv("PGPASSWORD", "")

    return create_engine(
        f"postgresql+psycopg2://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
    )


def _uniq(seq):
    """Preserve order while dropping duplicate column names."""
    return list(dict.fromkeys(seq))


def load_features_with_split(engine, features_view: str, split_view: str) -> pd.DataFrame:
    sql = f"""
        select
          f.*,
          s.split
        from {features_view} f
        join {split_view} s using (hadm_id)
    """

    raw = engine.raw_connection()
    try:
        return pd.read_sql_query(sql, raw)
    finally:
        raw.close()


def build_pipeline(continuous_cols, binary_cols, categorical_cols) -> Pipeline:
    cont_pipe = Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("sc", StandardScaler()),
    ])

    bin_pipe = Pipeline([
        ("imp", SimpleImputer(strategy="constant", fill_value=0)),
    ])

    cat_pipe = Pipeline([
        ("imp", SimpleImputer(strategy="most_frequent")),
        ("oh", OneHotEncoder(handle_unknown="ignore")),
    ])

    pre = ColumnTransformer([
        ("cont", cont_pipe, continuous_cols),
        ("bin", bin_pipe, binary_cols),
        ("cat", cat_pipe, categorical_cols),
    ], remainder="drop")

    clf = LogisticRegression(
        max_iter=4000,
        class_weight="balanced",
        solver="saga",
        n_jobs=-1,
        random_state=42,
    )

    return Pipeline([
        ("pre", pre),
        ("clf", clf),
    ])


def _drop_all_missing_train_cols(train: pd.DataFrame, cols: list[str]) -> tuple[list[str], list[str]]:
    kept = []
    dropped = []

    for c in cols:
        if c not in train.columns:
            dropped.append(c)
        elif train[c].notna().any():
            kept.append(c)
        else:
            dropped.append(c)

    return kept, dropped


def _check_preprocessed_nan(pipe: Pipeline, Xtr: pd.DataFrame, ytr: pd.Series) -> None:
    pre = pipe.named_steps["pre"]
    Xt = pre.fit_transform(Xtr, ytr)

    if hasattr(Xt, "toarray"):
        Xt_check = Xt.toarray()
    else:
        Xt_check = Xt

    if np.isnan(Xt_check).any():
        raw_missing = Xtr.isna().mean().sort_values(ascending=False)
        raise ValueError(
            "NaN still present after preprocessing.\n"
            f"Top raw missing rates:\n{raw_missing.head(20).to_string()}"
        )


def train_eval_save(
    *,
    features_view: str,
    split_view: str,
    out_dir: str,
    label: str,
    continuous_candidates: list[str],
    binary_candidates: list[str],
    categorical_candidates: list[str],
    drop_all_missing_train: bool = False,
    check_preprocessed_nan: bool = False,
    save_latest: bool = False,
):
    engine = make_engine()
    df = load_features_with_split(engine, features_view, split_view)

    missing_required = [x for x in ["split", label] if x not in df.columns]
    if missing_required:
        raise ValueError(f"Missing required columns in loaded data: {missing_required}")

    cont_cols = [c for c in _uniq(continuous_candidates) if c in df.columns]
    bin_cols = [c for c in _uniq(binary_candidates) if c in df.columns]
    cat_cols = [c for c in _uniq(categorical_candidates) if c in df.columns]

    train = df[df["split"] == "train"].copy()
    valid = df[df["split"] == "valid"].copy()

    if train.empty or valid.empty:
        raise ValueError("Train/valid split is empty.")

    dropped_cont = []
    dropped_bin = []
    dropped_cat = []

    if drop_all_missing_train:
        cont_cols, dropped_cont = _drop_all_missing_train_cols(train, cont_cols)
        bin_cols, dropped_bin = _drop_all_missing_train_cols(train, bin_cols)
        cat_cols, dropped_cat = _drop_all_missing_train_cols(train, cat_cols)

    used_cols = cont_cols + bin_cols + cat_cols

    if not used_cols:
        raise ValueError("No usable feature columns found. Check column names and missingness.")

    Xtr = train[used_cols]
    ytr = train[label].astype(int)

    Xva = valid[used_cols]
    yva = valid[label].astype(int)

    pipe = build_pipeline(cont_cols, bin_cols, cat_cols)

    if check_preprocessed_nan:
        _check_preprocessed_nan(pipe, Xtr, ytr)

    pipe.fit(Xtr, ytr)

    p_tr = pipe.predict_proba(Xtr)[:, 1]
    p_va = pipe.predict_proba(Xva)[:, 1]

    metrics = {
        "features_view": features_view,
        "split_view": split_view,
        "label": label,
        "train": {
            "auroc": float(roc_auc_score(ytr, p_tr)),
            "auprc": float(average_precision_score(ytr, p_tr)),
            "n": int(ytr.shape[0]),
        },
        "valid": {
            "auroc": float(roc_auc_score(yva, p_va)),
            "auprc": float(average_precision_score(yva, p_va)),
            "n": int(yva.shape[0]),
        },
        "features_used": used_cols,
        "continuous_used": cont_cols,
        "binary_used": bin_cols,
        "categorical_used": cat_cols,
    }

    if drop_all_missing_train:
        metrics["dropped_all_missing_train"] = {
            "continuous": dropped_cont,
            "binary": dropped_bin,
            "categorical": dropped_cat,
        }

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    (out / f"metrics_{stamp}.json").write_text(json.dumps(metrics, indent=2))
    dump(pipe, out / f"model_{stamp}.joblib")

    if save_latest:
        (out / "metrics_latest.json").write_text(json.dumps(metrics, indent=2))
        dump(pipe, out / "model_latest.joblib")

    print(json.dumps(metrics, indent=2))