#!/usr/bin/env python3

"""
Evaluate a trained logistic regression pipeline on the validation split.

This script loads a saved sklearn pipeline, reads a split view from PostgreSQL,
computes AUROC/AUPRC and threshold-based metrics, and saves an evaluation report
plus a histogram of validation predicted probabilities.
"""

import argparse
import json
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from joblib import load
from sqlalchemy import create_engine

from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
)


def make_engine():
    pg_host = os.getenv("PGHOST", "localhost")
    pg_port = os.getenv("PGPORT", "5432")
    pg_db = os.getenv("PGDATABASE", "mimic")
    pg_user = os.getenv("PGUSER", "mimicuser")
    pg_password = os.getenv("PGPASSWORD", "")

    return create_engine(
        f"postgresql+psycopg2://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
    )


def load_latest_model(model_dir: str):
    model_dir_path = Path(model_dir)

    latest_path = model_dir_path / "model_latest.joblib"
    if latest_path.exists():
        return str(latest_path), load(latest_path)

    models = sorted(model_dir_path.glob("model_*.joblib"))
    if not models:
        raise FileNotFoundError(f"No trained model found under {model_dir}")

    model_path = models[-1]
    return str(model_path), load(model_path)


def summarize_at_threshold(y_true, proba, threshold: float) -> dict:
    pred = (proba >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred).ravel()

    ppv = tp / (tp + fp + 1e-12)
    recall = tp / (tp + fn + 1e-12)
    specificity = tn / (tn + fp + 1e-12)
    f1 = 2 * ppv * recall / (ppv + recall + 1e-12)

    return {
        "threshold": float(threshold),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
        "ppv": float(ppv),
        "recall": float(recall),
        "specificity": float(specificity),
        "f1": float(f1),
        "alerts": int(tp + fp),
    }


def read_split_view(engine, split_view: str) -> pd.DataFrame:
    raw = engine.raw_connection()
    try:
        return pd.read_sql_query(f"select * from {split_view}", raw)
    finally:
        raw.close()


def main(model_dir: str, split_view: str, label: str = "y_inhosp_death"):
    engine = make_engine()
    model_path, model = load_latest_model(model_dir)

    df = read_split_view(engine, split_view)

    if "split" not in df.columns:
        raise ValueError(f"`split` column not found in {split_view}.")

    if label not in df.columns:
        raise ValueError(f"Label `{label}` not found in {split_view}.")

    valid = df[df["split"] == "valid"].copy()
    if valid.empty:
        raise ValueError("Validation split is empty.")

    y = valid[label].astype(int)

    # The trained ColumnTransformer selects the required feature columns by name.
    X = valid.drop(columns=[label, "split"], errors="ignore")

    proba = model.predict_proba(X)[:, 1]

    auroc = float(roc_auc_score(y, proba))
    auprc = float(average_precision_score(y, proba))

    precision, recall, thresholds = precision_recall_curve(y, proba)
    f1_curve = 2 * precision * recall / (precision + recall + 1e-12)
    best_ix = int(np.nanargmax(f1_curve))

    if len(thresholds) == 0:
        best_threshold = 0.5
    else:
        best_threshold = float(thresholds[max(0, best_ix - 1)])

    summary_at_05 = summarize_at_threshold(y, proba, 0.5)
    summary_at_best_f1 = summarize_at_threshold(y, proba, best_threshold)

    fig_dir = Path(model_dir) / "figs"
    fig_dir.mkdir(parents=True, exist_ok=True)

    hist_path = fig_dir / "valid_proba_hist.png"

    plt.figure()
    plt.hist(proba, bins=50)
    plt.title("Validation predicted probabilities")
    plt.xlabel("Predicted probability of in-hospital death")
    plt.ylabel("Count")
    plt.savefig(hist_path, bbox_inches="tight")
    plt.close()

    report = {
        "model_dir": model_dir,
        "model_path": model_path,
        "split_view": split_view,
        "label": label,
        "valid_n": int(y.shape[0]),
        "valid_prevalence": float(y.mean()),
        "auroc": auroc,
        "auprc": auprc,
        "best_threshold_by_f1": float(best_threshold),
        "summary_at_0_5": summary_at_05,
        "summary_at_best_f1": summary_at_best_f1,
        "histogram": str(hist_path),
    }

    eval_path = Path(model_dir) / "eval_latest.json"
    eval_path.write_text(json.dumps(report, indent=2))

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_dir",
        required=True,
        help="Artifact directory containing model_*.joblib or model_latest.joblib",
    )
    parser.add_argument(
        "--split_view",
        required=True,
        help="Split view, such as features.split_v3 or features.split_v5_icu",
    )
    parser.add_argument(
        "--label",
        default="y_inhosp_death",
    )

    args = parser.parse_args()

    main(
        model_dir=args.model_dir,
        split_view=args.split_view,
        label=args.label,
    )