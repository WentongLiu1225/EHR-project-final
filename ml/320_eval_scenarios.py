#!/usr/bin/env python3

"""
Evaluate a trained model under multiple decision scenarios.

This script loads a saved model, applies it to the validation split, computes
global metrics, and evaluates decision performance under best-F1, fixed-recall,
and top-K alert settings.

It also saves validation predictions for downstream FP/FN error analysis.
Generated row-level prediction files should not be uploaded to GitHub.
"""

import argparse
import json
import os
from pathlib import Path

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


EPS = 1e-12


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
        raise FileNotFoundError(
            f"No model_latest.joblib or model_*.joblib found under {model_dir}"
        )

    model_path = models[-1]
    return str(model_path), load(model_path)


def summarize_at_threshold(y_true, p_pred, threshold: float) -> dict:
    pred = (p_pred >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred).ravel()

    ppv = tp / (tp + fp + EPS)
    recall = tp / (tp + fn + EPS)
    specificity = tn / (tn + fp + EPS)
    f1 = 2 * ppv * recall / (ppv + recall + EPS)

    return {
        "threshold": float(threshold),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
        "ppv": float(ppv),
        "recall": float(recall),
        "specificity": float(specificity),
        "f1": float(f1),
        "alerts": int(tp + fp),
    }


def threshold_for_recall(y_true, p_pred, target_recall: float) -> float:
    """
    Choose the largest threshold that still reaches the target recall.
    """
    _precision, recall, thresholds = precision_recall_curve(y_true, p_pred)

    if len(thresholds) == 0:
        return 0.5

    recall_at_thresholds = recall[1:]
    ok = np.where(recall_at_thresholds >= target_recall)[0]

    if len(ok) == 0:
        return float(thresholds[0])

    return float(thresholds[ok[-1]])


def threshold_for_topk(p_pred, k: int) -> float:
    """
    Use the score at rank k as the threshold for a top-K alert rule.
    """
    n = len(p_pred)

    if k <= 0:
        return 1.0

    if k >= n:
        return 0.0

    sorted_scores = np.sort(p_pred)[::-1]
    return float(sorted_scores[k - 1])


def best_threshold_by_f1(y_true, p_pred) -> float:
    precision, recall, thresholds = precision_recall_curve(y_true, p_pred)

    if len(thresholds) == 0:
        return 0.5

    precision_at_thresholds = precision[1:]
    recall_at_thresholds = recall[1:]

    f1 = (
        2
        * precision_at_thresholds
        * recall_at_thresholds
        / (precision_at_thresholds + recall_at_thresholds + EPS)
    )

    best_index = int(np.nanargmax(f1))
    return float(thresholds[best_index])


def get_column_transformer_cols(pre, name: str) -> list[str]:
    for transformer_name, _transformer, cols in pre.transformers_:
        if transformer_name == name:
            return list(cols) if cols is not None else []

    return []


def get_pipeline_feature_cols(pipe, df: pd.DataFrame) -> list[str]:
    """
    Extract raw feature columns used by the fitted pipeline.

    This avoids passing ID, time, label, or split columns into predict_proba.
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


def add_prediction_columns(
    valid_df: pd.DataFrame,
    proba: np.ndarray,
) -> pd.DataFrame:
    """
    Add prediction probability, threshold-0.5 label, and descending risk rank.
    """
    df_out = valid_df.copy()

    df_out["y_pred_proba"] = proba
    df_out["y_pred_label_05"] = (df_out["y_pred_proba"] >= 0.5).astype(int)

    df_out = df_out.sort_values(by="y_pred_proba", ascending=False)
    df_out = df_out.reset_index(drop=True)
    df_out["rank_desc"] = df_out.index + 1

    return df_out


def save_prediction_artifact(valid_df_with_pred: pd.DataFrame, model_dir: str) -> str:
    """
    Save row-level validation predictions for downstream error analysis.
    Do not upload this output to GitHub.
    """
    output_path = Path(model_dir) / "valid_predictions_detailed.csv"
    valid_df_with_pred.to_csv(output_path, index=False)

    return str(output_path)


def read_split_view(engine, split_view: str) -> pd.DataFrame:
    raw_conn = engine.raw_connection()
    try:
        return pd.read_sql_query(f"select * from {split_view}", raw_conn)
    finally:
        raw_conn.close()


def main(model_dir: str, split_view: str, label: str, recalls, topks):
    engine = make_engine()
    model_path, model = load_latest_model(model_dir)

    df = read_split_view(engine, split_view)

    if "split" not in df.columns:
        raise ValueError(f"`split` column not found in {split_view}.")

    if label not in df.columns:
        raise ValueError(f"Label `{label}` not found in {split_view}.")

    valid_df = df[df["split"] == "valid"].copy()
    if valid_df.empty:
        raise ValueError("Validation split is empty.")

    y_true = valid_df[label].astype(int).to_numpy()

    feature_cols = get_pipeline_feature_cols(model, valid_df)
    X_valid = valid_df[feature_cols].copy()

    y_pred_proba = model.predict_proba(X_valid)[:, 1]

    auroc = float(roc_auc_score(y_true, y_pred_proba))
    auprc = float(average_precision_score(y_true, y_pred_proba))

    valid_df_scored = add_prediction_columns(valid_df, y_pred_proba)
    prediction_csv_path = save_prediction_artifact(valid_df_scored, model_dir)

    scenarios = {}

    best_f1_threshold = best_threshold_by_f1(y_true, y_pred_proba)
    scenarios["F1_best"] = summarize_at_threshold(
        y_true,
        y_pred_proba,
        best_f1_threshold,
    )

    for target_recall in recalls:
        threshold = threshold_for_recall(y_true, y_pred_proba, target_recall)
        scenario_name = f"Recall_{int(target_recall * 100)}%"
        scenarios[scenario_name] = summarize_at_threshold(
            y_true,
            y_pred_proba,
            threshold,
        )

    for top_k in topks:
        threshold = threshold_for_topk(y_pred_proba, top_k)
        scenario_name = f"Top{top_k}"
        scenarios[scenario_name] = summarize_at_threshold(
            y_true,
            y_pred_proba,
            threshold,
        )

    output_json_path = Path(model_dir) / "eval_scenarios_latest.json"
    output_csv_path = Path(model_dir) / "eval_scenarios_latest.csv"

    report = {
        "model_dir": model_dir,
        "model_path": model_path,
        "split_view": split_view,
        "label": label,
        "n_valid": int(len(valid_df)),
        "prevalence_valid": float(y_true.mean()),
        "auroc": auroc,
        "auprc": auprc,
        "valid_predictions_csv": prediction_csv_path,
        "features_used_for_prediction": feature_cols,
        "scenarios": scenarios,
    }

    output_json_path.write_text(json.dumps(report, indent=2))

    scenario_rows = []
    for scenario_name, scenario_result in scenarios.items():
        scenario_rows.append({
            "scenario": scenario_name,
            "threshold": scenario_result["threshold"],
            "ppv": scenario_result["ppv"],
            "recall": scenario_result["recall"],
            "specificity": scenario_result["specificity"],
            "f1": scenario_result["f1"],
            "alerts": scenario_result["alerts"],
            "tn": scenario_result["confusion_matrix"][0][0],
            "fp": scenario_result["confusion_matrix"][0][1],
            "fn": scenario_result["confusion_matrix"][1][0],
            "tp": scenario_result["confusion_matrix"][1][1],
        })

    pd.DataFrame(scenario_rows).to_csv(output_csv_path, index=False)

    print(json.dumps({
        "saved_json": str(output_json_path),
        "saved_csv": str(output_csv_path),
        "saved_predictions": prediction_csv_path,
        "auroc": auroc,
        "auprc": auprc,
        "n_features_used": len(feature_cols),
        "scenarios": list(scenarios.keys()),
    }, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_dir", required=True)
    parser.add_argument(
        "--split_view",
        required=True,
        help="Split view, such as features.split_v3 or features.split_v5_icu",
    )
    parser.add_argument("--label", default="y_inhosp_death")
    parser.add_argument("--recalls", default="0.4,0.5,0.6")
    parser.add_argument("--topks", default="1000,3000")

    args = parser.parse_args()

    recalls = [float(x) for x in args.recalls.split(",") if x.strip()]
    topks = [int(x) for x in args.topks.split(",") if x.strip()]

    main(
        model_dir=args.model_dir,
        split_view=args.split_view,
        label=args.label,
        recalls=recalls,
        topks=topks,
    )