# Early In-Hospital Mortality Prediction using MIMIC-IV

This project builds an early in-hospital mortality prediction pipeline using MIMIC-IV data. The goal is to predict in-hospital mortality using admission-time and first-24h EHR information, while avoiding features that would only be known later in the hospitalization.

The project started as a hospital-wide model and then moved toward separate ICU and non-ICU models.

## Project Overview

The main unit of analysis is one hospital admission, identified by `hadm_id`. The outcome is in-hospital mortality.

I built the feature sets as SQL views/tables under the `features` schema and trained both logistic regression and XGBoost models. Model performance was evaluated using AUROC, AUPRC, fixed-recall scenarios, fixed-alert-budget scenarios, SHAP explainability, and post-model error analysis.

## Modeling Roadmap

- V1: Core hospital-wide baseline using age, selected first-24h labs, and Charlson score
- V2: Added broader first-24h labs and lab missingness indicators
- V3: Added early medication/procedure signals and chronic disease indicators
- V4: Added vital-sign summaries as a hospital-wide feasibility check
- V5: ICU-only model using first ICU stay vital signs
- V6: Non-ICU model without ICU-derived vital features

## Main Findings

From V1 to V3, model performance improved as more early clinical information was added. XGBoost generally performed better than logistic regression across model versions.

V4 showed that vital signs were useful for prediction, but the coverage check showed that these features were mostly available for ICU admissions and largely missing for non-ICU admissions. Because of that, I treated V4 as a feasibility check rather than the final hospital-wide model.

The final modeling direction separates the task into ICU and non-ICU models. This makes the modeling setup more consistent with the data actually available in each care setting.

## Key Validation Results

| Model  | Cohort                          | Valid N | Valid Prevalence | AUROC | AUPRC |
|:-------|:--------------------------------|--------:|-----------------:|------:|------:|
| XGB V3 | Hospital-wide                   | 291,856 |            0.021 | 0.903 | 0.302 |
| XGB V4 | Hospital-wide feasibility check | 291,856 |            0.021 | 0.926 | 0.385 |
| XGB V5 | ICU-only                        |  44,757 |            0.110 | 0.869 | 0.535 |
| XGB V6 | Non-ICU                         | 247,099 |            0.005 | 0.890 | 0.075 |

The ICU and non-ICU models should not be compared directly because the outcome prevalence and data availability are very different.

## Repository Structure

- `reports/`: full project report
- `sql/`: SQL scripts for cohort construction, feature engineering, and data checks
- `ml/`: Python scripts for model training, evaluation, SHAP, and error analysis
- `results/`: aggregate result summaries only
- `figures/`: summary figures and SHAP plots
- `config/`: example configuration template

## Data Access Note

This project uses MIMIC-IV, which requires credentialed access through PhysioNet. Raw data, row-level derived datasets, row-level predictions, and case-level review files are not included in this repository.

## Current Status

This repository is being organized for portfolio and interview review. The report and scripts are included to show the full modeling workflow from feature construction to model evaluation and error analysis.

