#!/usr/bin/env python3

"""

Common XGBoost training utilities for the in-hospital mortality project.

The version-specific XGBoost scripts pass in a SQL split view and feature lists.
This file loads the data, prepares the selected features, trains an XGBoost
classifier with early stopping, evaluates AUROC/AUPRC, and saves the model and
metrics.

"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from joblib import dump
from sqlalchemy import create_engine

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from xgboost import XGBClassifier


def make_engine():
    pg_host = os.getenv("PGHOST", "localhost")
    pg_port = os.getenv("PGPORT", "5432")
    pg_db = os.getenv("PGDATABASE", "mimic")
    pg_user = os.getenv("PGUSER", "mimicuser")
    pg_password = os.getenv("PGPASSWORD", "")

    return create_engine(
        f"postgresql+psycopg2://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
    )


def read_sql(engine, sql: str) -> pd.DataFrame:
    raw = engine.raw_connection()
    try:
        return pd.read_sql_query(sql, raw)
    finally:
        raw.close()


def compute_scale_pos_weight(y: pd.Series) -> float:
    pos = int(y.sum())
    neg = int(y.shape[0] - pos)

    return float(neg / max(1, pos))


def latest_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def select_existing(df: pd.DataFrame, candidates: List[str]) -> List[str]:
    return [c for c in candidates if c in df.columns]


def build_preprocessor(
    num_cols: List[str],
    cat_cols: List[str],
) -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="median"), num_cols),
            (
                "cat",
                Pipeline(steps=[
                    ("imp", SimpleImputer(strategy="most_frequent")),
                    ("oh", OneHotEncoder(handle_unknown="ignore")),
                ]),
                cat_cols,
            ),
        ],
        remainder="drop",
    )


def train_xgb_on_split_df(
    df: pd.DataFrame,
    *,
    label: str,
    split_col: str,
    num_candidates: List[str],
    cat_candidates: List[str],
    out_dir: str,
    n_jobs: int = 4,
    xgb_params: Optional[Dict] = None,
) -> Tuple[str, str]:
    """
    Train an XGBoost model using a precomputed train/valid split column.

    Saves timestamped and latest model/metric artifacts into out_dir.
    Returns the timestamped model path and metrics path.
    """
    if split_col not in df.columns:
        raise ValueError(f"Split view must contain `{split_col}` with values train/valid.")

    if label not in df.columns:
        raise ValueError(f"Label `{label}` not found in the split view.")

    num_cols = select_existing(df, num_candidates)
    cat_cols = select_existing(df, cat_candidates)

    used_cols = num_cols + cat_cols
    if not used_cols:
        raise ValueError("No feature columns found.")

    train = df[df[split_col] == "train"].copy()
    valid = df[df[split_col] == "valid"].copy()

    if train.empty or valid.empty:
        raise ValueError("Train/valid split is empty. Check split values in the split view.")

    Xtr = train[used_cols]
    ytr = train[label].astype(int)

    Xva = valid[used_cols]
    yva = valid[label].astype(int)

    scale_pos_weight = compute_scale_pos_weight(ytr)

    pre = build_preprocessor(
        num_cols=num_cols,
        cat_cols=cat_cols,
    )

    # Fit the preprocessor first so XGBoost can use the transformed validation set
    # for early stopping.
    pre.fit(Xtr, ytr)
    Xtr_transformed = pre.transform(Xtr)
    Xva_transformed = pre.transform(Xva)

    default_xgb_params = {
        "n_estimators": 5000,
        "max_depth": 4,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "objective": "binary:logistic",
        "eval_metric": "aucpr",
        "tree_method": "hist",
        "n_jobs": n_jobs,
        "scale_pos_weight": scale_pos_weight,
        "random_state": 42,
        "early_stopping_rounds": 50,
    }

    if xgb_params:
        default_xgb_params.update(xgb_params)

    xgb = XGBClassifier(**default_xgb_params)
    xgb.fit(
        Xtr_transformed,
        ytr,
        eval_set=[(Xva_transformed, yva)],
        verbose=False,
    )

    pipe = Pipeline([
        ("pre", pre),
        ("xgb", xgb),
    ])

    proba_tr = pipe.predict_proba(Xtr)[:, 1]
    proba_va = pipe.predict_proba(Xva)[:, 1]

    metrics = {
        "label": label,
        "split_col": split_col,
        "train": {
            "auroc": float(roc_auc_score(ytr, proba_tr)),
            "auprc": float(average_precision_score(ytr, proba_tr)),
            "n": int(ytr.shape[0]),
            "prevalence": float(ytr.mean()),
        },
        "valid": {
            "auroc": float(roc_auc_score(yva, proba_va)),
            "auprc": float(average_precision_score(yva, proba_va)),
            "n": int(yva.shape[0]),
            "prevalence": float(yva.mean()),
        },
        "scale_pos_weight": float(scale_pos_weight),
        "best_iteration": int(getattr(xgb, "best_iteration", -1)),
        "best_score": float(getattr(xgb, "best_score", np.nan)),
        "features_used": used_cols,
        "continuous_used": num_cols,
        "categorical_used": cat_cols,
    }

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    stamp = latest_stamp()

    model_path = out_path / f"model_{stamp}.joblib"
    metrics_path = out_path / f"metrics_{stamp}.json"

    dump(pipe, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2))

    dump(pipe, out_path / "model_latest.joblib")
    (out_path / "metrics_latest.json").write_text(json.dumps(metrics, indent=2))

    print(json.dumps({
        "out_dir": str(out_path),
        "saved_model": str(model_path),
        "saved_metrics": str(metrics_path),
        "train_auroc": metrics["train"]["auroc"],
        "train_auprc": metrics["train"]["auprc"],
        "valid_auroc": metrics["valid"]["auroc"],
        "valid_auprc": metrics["valid"]["auprc"],
        "best_iteration": metrics["best_iteration"],
        "n_features_raw": len(used_cols),
    }, indent=2))

    return str(model_path), str(metrics_path)


def train_from_split_view(
    *,
    split_view: str,
    label: str,
    out_dir: str,
    num_candidates: List[str],
    cat_candidates: List[str],
    split_col: str = "split",
    n_jobs: int = 4,
    xgb_params: Optional[Dict] = None,
):
    engine = make_engine()
    df = read_sql(engine, f"select * from {split_view}")

    return train_xgb_on_split_df(
        df,
        label=label,
        split_col=split_col,
        num_candidates=num_candidates,
        cat_candidates=cat_candidates,
        out_dir=out_dir,
        n_jobs=n_jobs,
        xgb_params=xgb_params,
    )