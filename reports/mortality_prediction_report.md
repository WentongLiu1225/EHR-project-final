## Modeling Roadmap: From Feature Expansion to Care-Setting-Specific Models

### Stage 1 — Core hospital-wide baseline

Stage 1 was the starting point of the project. I used it as a simple hospital-wide baseline before adding larger lab panels, missingness indicators, treatment signals, or vital signs.

In this stage, I only used a small set of early clinical variables:

- **Clinical context:** `age_at_admit`
- **Early labs:** first available lab values within 24 hours after admission: `sodium_24h_first`, `potassium_24h_first`, `creatinine_24h_first`, `lactate_24h_first`
- **Comorbidity summary:** `charlson_min`
- **Label:** `y_inhosp_death`
- **Split:** time-based split using `features.split`
- **Feature view:** `features.inhosp_mortality_features`

I intentionally left out demographic and administrative variables, including `gender`, `insurance`, `admission_type`, `admission_location`, `race`, and `language`. The goal was to keep the first model focused on basic first-24h clinical signal, instead of relying on demographic or workflow-related variables.

In the validation set, Stage 1 included 291,856 admissions, with an in-hospital mortality prevalence of about 2.1%. The logistic regression model reached an AUROC of **0.778** and an AUPRC of **0.162**. The XGBoost model performed better, with an AUROC of **0.842** and an AUPRC of **0.211**.


### Stage 2 — Extended first-24h labs and lab missingness

Stage 2 kept the same basic structure as Stage 1, but expanded the lab information available in the first 24 hours. In addition to age, the four core labs, and `charlson_min`, I added a broader chemistry and CBC panel and created missingness indicators for each lab.

The added lab values included:

- `glucose_24h_first`
- `bun_24h_first`
- `chloride_24h_first`
- `bicarbonate_24h_first`
- `calcium_24h_first`
- `magnesium_24h_first`
- `phosphate_24h_first`
- `wbc_24h_first`
- `hemoglobin_24h_first`
- `platelets_24h_first`

For each lab in the V2 panel, I also added a binary missingness flag, where 1 means the lab was not available within the first 24 hours. I included these flags because whether a lab was ordered can carry information about early clinical concern, not just the lab value itself.

As in Stage 1, I did not include demographic or administrative variables such as `gender`, `insurance`, `admission_type`, `admission_location`, `race`, or `language`. I used the same rule for the later stages, so I will not repeat this point for every version below.

The feature view for this stage was `features.inhosp_mortality_features_v2`, and the time-based split was stored in `features.split_v2`.

In the validation set, Stage 2 again included 291,856 admissions, with an in-hospital mortality prevalence of about 2.1%. The logistic regression model improved to an AUROC of **0.858** and an AUPRC of **0.186**. The XGBoost model reached an AUROC of **0.879** and an AUPRC of **0.254**.

### Stage 3 — Early-care signals and chronic disease burden

Stage 3 kept the Stage 2 lab panel and missingness flags, then added two types of information that could better reflect patient severity: early-care intensity and chronic disease burden.

The new early-care features included medication group flags based on prescriptions started within the first 24 hours:

- `vasopressor_24h`
- `antibiotic_24h`
- `insulin_24h`
- `diuretic_24h`
- `anticoag_antiplatelet_24h`
- `sedative_analgesic_24h`

I also added ICU-recorded procedure flags within the first 24 hours:

- `airway_intubation_24h`
- `central_line_24h`
- `arterial_line_24h`
- `dialysis_24h`
- `chest_tube_24h`

Finally, I added several chronic diagnosis group indicators:

- `copd`
- `chronic_liver`
- `malignancy`
- `cerebrovascular`
- `hypertension`
- `cad`

The feature view for this stage was `features.inhosp_mortality_features_v3`, and the time-based split was stored in `features.split_v3`.

The goal of this stage was to keep the same first-24h window, but add information that could reflect early treatment intensity and baseline disease burden. This helped move the model beyond labs alone, while still avoiding variables that would only be known later in the admission.

In the validation set, Stage 3 included 291,856 admissions, with an in-hospital mortality prevalence of about 2.1%. The logistic regression model improved to an AUROC of **0.894** and an AUPRC of **0.244**. The XGBoost model reached an AUROC of **0.903** and an AUPRC of **0.302**.

### Stage 4 — Hospital-wide vitals feasibility check

After Stage 3, I tested whether adding vital-sign summaries could further improve the hospital-wide model. These vital signs were derived from ICU chart events, so I treated this step partly as a coverage check. Because vital signs are closely related to patient acuity, I created first/min/max summaries for six vital signs within the first 24 hours after hospital admission:

- Heart rate: `hr_24h_first`, `hr_24h_min`, `hr_24h_max`
- Respiratory rate: `rr_24h_first`, `rr_24h_min`, `rr_24h_max`
- Systolic blood pressure: `sbp_24h_first`, `sbp_24h_min`, `sbp_24h_max`
- Diastolic blood pressure: `dbp_24h_first`, `dbp_24h_min`, `dbp_24h_max`
- Oxygen saturation: `spo2_24h_first`, `spo2_24h_min`, `spo2_24h_max`
- Temperature: `temp_24h_first`, `temp_24h_min`, `temp_24h_max`

I also added missingness flags for each vital-sign group.

The feature view for this stage was `features.inhosp_mortality_features_v4`, and the time-based split was stored in `features.split_v4`.

In the validation set, Stage 4 included 291,856 admissions, with an in-hospital mortality prevalence of about 2.1%. The logistic regression model reached an AUROC of **0.907** and an AUPRC of **0.287**. The XGBoost model reached an AUROC of **0.926** and an AUPRC of **0.385**.

Although Stage 4 improved performance, the coverage check showed an important limitation. In the full hospital-wide cohort, only **12.5%** of admissions had any of these vital-sign features available, and **87.5%** had all vital signs missing. When I split the cohort by ICU status, the issue became clearer: ICU admissions had much better vital coverage, while non-ICU admissions had these ICU-derived vitals missing for almost all patients.

Because of that, I treated Stage 4 as a feasibility check rather than the final hospital-wide model. It showed that vitals were useful, but also that they should not be added blindly to the full cohort. This led to the next step: separating the problem into ICU and non-ICU models.

### Stage 5 — ICU-only admission-level model with vital signs

Stage 5 focused only on ICU admissions. The goal was to use vital-sign information in the setting where it was actually available and clinically meaningful.

One issue I found during data checking was that some hospital admissions had more than one ICU stay. To keep the unit of analysis consistent with the rest of the project, I kept the model at the hospital-admission level. For admissions with multiple ICU stays, I selected the first ICU stay and summarized vital signs from the first 24 hours after that ICU stay started.

This means Stage 5 is still one row per `hadm_id`, but the ICU vital-sign features come from the first ICU stay during that admission.

The Stage 5 feature set included:

- age, first-24h labs and lab missingness indicators
- selected early medication and procedure flags
- chronic diagnosis group indicators
- first/min/max ICU vital-sign summaries
- vital-sign missingness indicator

The feature table was `features.inhosp_mortality_features_v5_icu`, and the split table was `features.split_v5_icu`.

After updating the dataset to one row per hospital admission, Stage 5 had 85,242 ICU admissions. The validation set included 44,757 admissions, with an in-hospital mortality prevalence of about 11.0%.

The logistic regression model reached an AUROC of **0.824** and an AUPRC of **0.414**. The XGBoost model performed better, with an AUROC of **0.869** and an AUPRC of **0.535**.

This stage is important because it uses the vital-sign features in the population where they make the most sense. It also avoids repeating the same hospital admission multiple times just because the patient had more than one ICU stay.

### Stage 6 — Non-ICU admission-level model

Stage 6 was built as the non-ICU version of the care-setting-specific model. I added this stage because the Stage 4 coverage check showed that ICU-derived vital signs were not available for non-ICU admissions.

For this stage, I excluded admissions with any ICU stay and kept the unit of analysis at the hospital-admission level, with one row per `hadm_id`. The feature set stayed close to Stage 3: first-24h labs, lab missingness flags, selected early medication/procedure indicators, and chronic diagnosis group indicators. I did not include ICU vital-sign features in this model.

The feature table was `features.inhosp_mortality_features_v6_nonicu`, and the split table was `features.split_v6_nonicu`.

The non-ICU cohort had a much lower mortality rate than the ICU cohort. In the validation set, Stage 6 included 247,099 admissions, with an in-hospital mortality prevalence of about 0.5%.

The logistic regression model reached an AUROC of **0.883** and an AUPRC of **0.056**. The XGBoost model reached an AUROC of **0.890** and an AUPRC of **0.075**.

The AUPRC is much lower than in the ICU-only model, but this is expected because the outcome is much rarer in the non-ICU cohort. I interpret the ICU and non-ICU models separately, rather than treating them as a direct head-to-head comparison.

### Summary of the roadmap

Overall, the project started with a hospital-wide first-24h baseline and gradually added more clinical information. Stages 1–3 show how performance changed after adding broader labs, missingness indicators, early-care signals, and chronic diagnosis groups. Stage 4 tested whether vital signs could improve the hospital-wide model, but the coverage check showed that these ICU-derived vital signs were mostly unavailable outside the ICU. Based on that finding, I split the later work into two care-setting-specific models: an ICU-only model that used vital signs from the first ICU stay, and a non-ICU model that did not include ICU-derived vital-sign features.

---

# EHR In-Hospital Mortality Prediction: A Care-Setting-Specific Modeling Pipeline

> **TL;DR**  
> **Objective:** Predict in-hospital mortality using information available at admission or early in the hospital/ICU course, with a focus on avoiding leakage from later hospitalization events.  
> **Data source:** MIMIC-IV loaded in a local PostgreSQL database. In my current runs, the database name is mimic. Cohorts and predictors are built as versioned feature views under the features schema.
>
> **Main idea:** I first built a hospital-wide model in stages, starting from a small first-24h clinical baseline and then adding expanded labs, missingness flags, early-care signals, and chronic diagnosis groups. I then tested whether vital signs could be added to the full hospital-wide cohort. That V4 check shows that ICU-derived vitals were useful but not evenly available across all admissions, so I split the later work into two care-setting-specific models: an ICU-only model using vital signs from the first ICU stay, and a non-ICU model without ICU-derived vital-sign features.
>
> **Key findings:** XGBoost generally outperformed logistic regression across model versions. The hospital-wide V4 model had the strongest overall hospital-wide performance, but I treated it as a feasibility check because vital-sign coverage was highly uneven. The final care-setting-specific models made more sense from a data-availability standpoint: V5 focused on ICU admissions with dense vital-sign monitoring, while V6 focused on non-ICU admissions where ICU-derived vitals were not available for almost all admissions.


---

## 1. Data & Cohort

**Data source:** MIMIC-IV, a publicly available de-identified EHR dataset from PhysioNet. In this project, I loaded the data into a local PostgreSQL database named `mimic` and used SQL views under the `features` schema to build the modeling cohorts.

**Outcome:** `y_inhosp_death`, defined as 1 if the patient died during the hospital admission and 0 otherwise.

**Main unit of analysis:** One hospital admission per row, identified by `hadm_id`.

For the hospital-wide and non-ICU models, predictors were restricted to information available at admission or within the first 24 hours after hospital admission. For the ICU-only model, I kept the unit at the hospital-admission level, but selected the first ICU stay for each admission and summarized vital signs from the first 24 hours after ICU `intime`.

This setup keeps the project focused on early risk prediction and avoids using information that would only be known later in the hospitalization.

### Versioned feature views

I built the modeling datasets as versioned feature views or tables under the `features` schema.

- **V1 / Stage 1 — Core hospital-wide baseline**  
  View: `features.inhosp_mortality_features`  
  This version includes age, a small set of first-24h labs, and `charlson_min`.

- **V2 / Stage 2 — Extended first-24h labs + lab missingness**  
  View: `features.inhosp_mortality_features_v2`  
  This version keeps V1 and adds a broader first-24h lab panel plus missingness indicators for each lab.

- **V3 / Stage 3 — Early-care signals + chronic diagnosis groups**  
  View: `features.inhosp_mortality_features_v3`  
  This version keeps V2 and adds early medication flags, procedure flags, and chronic diagnosis group indicators.

- **V4 / Stage 4 — Hospital-wide vitals feasibility check**  
  View: `features.inhosp_mortality_features_v4`  
  This version adds first/min/max vital-sign summaries and vital missingness flags to V3. I used this stage mainly to check whether ICU-derived vital signs could be used in the full hospital-wide cohort.

- **V5 / Stage 5 — ICU-only admission-level model**  
  Table: `features.inhosp_mortality_features_v5_icu`  
  This version focuses on ICU admissions. For admissions with multiple ICU stays, I selected the first ICU stay and added first/min/max ICU vital-sign summaries from the first 24 hours after ICU `intime`.

- **V6 / Stage 6 — Non-ICU admission-level model**  
  Table: `features.inhosp_mortality_features_v6_nonicu`  
  This version excludes admissions with any ICU stay and keeps a Stage 3-style feature set without ICU vital-sign features.

### Train/Validation split

I used a time-based train/validation split based on `anchor_year`:

- `anchor_year < 2150` → `train`
- `anchor_year >= 2150` → `valid`

Each model version has its own split table, so the split stays tied to the corresponding feature version:

- `features.split`
- `features.split_v2`
- `features.split_v3`
- `features.split_v4`
- `features.split_v5_icu`
- `features.split_v6_nonicu`

For V5, I reused the V4 split assignment at the `hadm_id` level after converting the ICU feature table to one row per hospital admission. This kept the ICU model aligned with the same time-based split logic while avoiding repeated rows for admissions with multiple ICU stays.

### Data checks before modeling

Before and during model building, I ran a set of basic data checks, including the following:

- I checked that the feature table and split table matched at the admission level.
- `hadm_id` was unique in each admission-level modeling table.
- For V5, I confirmed that the ICU feature table was no longer ICU-stay-level. After selecting the first ICU stay per admission, `features.inhosp_mortality_features_v5_icu` had one row per `hadm_id`.
- For V6, I confirmed that the cohort excluded ICU admissions and remained one row per `hadm_id`.
- I also checked outcome prevalence in train and validation splits to make sure there was no obvious split imbalance.

These checks helped catch one important issue during the V5 update: the first ICU version was originally one row per `stay_id`, which duplicated some hospital admissions. I corrected this by selecting the first ICU stay per `hadm_id` before rebuilding the V5 feature table and split table.

---

## 2. Features

This section summarizes the main feature types and naming conventions used across the model versions. The detailed version-by-version feature changes are described in the roadmap above.

### 2.1 Core clinical features

The core feature set starts with a small number of early clinical variables:

- `age_at_admit`
- `charlson_min`, a minimal Charlson-style comorbidity score
- selected first-24h lab values

Lab values use the naming pattern `*_24h_first`, which means the first available value within the first 24 hours after admission. For example, `creatinine_24h_first` is the first creatinine value measured within the first 24 hours.

### 2.2 Lab values and missingness flags

From Stage 2 onward, I used a broader first-24h lab panel, including chemistry and CBC variables such as BUN, bicarbonate, WBC, hemoglobin, and platelets.

For each lab, I also created a missingness flag using the pattern `*_24h_missing`, where 1 means the lab was not available within the first 24 hours. I included these flags because missingness is not always random in EHR data. Whether a lab was ordered can reflect early clinical concern, workflow, or patient acuity.

### 2.3 Early-care and chronic disease features

Stage 3 added early-care signals and chronic diagnosis group indicators.

The early-care features include grouped medication flags based on prescriptions started within the first 24 hours such as `vasopressor_24h`, `antibiotic_24h`, and `sedative_analgesic_24h`, as well as procedure flags such as `airway_intubation_24h`, `central_line_24h`, `dialysis_24h`, and `chest_tube_24h`.

The chronic disease features are ICD-derived diagnosis group indicators, including `copd`, `chronic_liver`, `malignancy`, `cerebrovascular`, `hypertension`, and `cad`.

### 2.4 Vital-sign features

Stage 4 tested whether vital-sign summaries could be added to the hospital-wide model. These vital signs were derived from ICU chart events, so I treated this stage as a feasibility check. These features used the same first-24h idea and included first, minimum, and maximum values for heart rate, respiratory rate, systolic and diastolic blood pressure, oxygen saturation, and temperature.

The vital-sign feature names follow the same pattern:

- `*_24h_first`
- `*_24h_min`
- `*_24h_max`
- `*_24h_missing`

For example, `spo2_24h_min` is the minimum oxygen saturation value in the first 24 hours.

Data checks showed that these vital-sign features were mainly available for ICU admissions. Because of that, I used Stage 4 as a feasibility check and then separated the later models into ICU and non-ICU cohorts.

### 2.5 Care-setting-specific feature use

For the ICU-only model, I kept the unit of analysis at the hospital-admission level but selected the first ICU stay for each admission. The ICU model used selected Stage 3 features plus ICU vital-sign summaries from the first 24 hours after ICU `intime`.

For the non-ICU model, I excluded admissions with any ICU stay and did not include ICU vital-sign features. This kept the non-ICU model aligned with the type of data available in that setting.


---

## 3. Models & Training

I trained each model using the same general training workflow. Each training script reads from the matching split table, applies the preprocessing steps, fits the model, evaluates it on the validation set, and saves the model artifacts under `artifacts/`.

The overall workflow is:

`feature table → split table → preprocessing → model training → validation metrics → scenario evaluation → SHAP / error analysis`

This structure made it easier to rerun a specific model, compare results across versions and check which features were actually used in each run.

### 3.1 Logistic Regression

I used logistic regression as the linear baseline model.

- **Model:** `sklearn.linear_model.LogisticRegression`
- **Class imbalance:** handled with `class_weight="balanced"`
- **Numeric preprocessing:** median imputation + standardization
- **Categorical preprocessing:** supported in the pipeline with most-frequent imputation and one-hot encoding, although the main no-demographic runs did not use categorical variables
- **Binary preprocessing:** missing values filled with 0
- **Outputs:** saved model and metrics under `artifacts/logit_*`

### 3.2 XGBoost

I used XGBoost as the non-linear model because it can capture interactions and non-linear patterns that logistic regression may miss.

- **Model:** `xgboost.XGBClassifier`
- **Objective:** `binary:logistic`
- **Numeric preprocessing:** median imputation
- **Categorical preprocessing:** most-frequent imputation + one-hot encoding, if categorical variables were used
- **Class imbalance:** `scale_pos_weight = #negative / #positive`, computed from the training split
- **Early stopping:** the validation split was used for early stopping during XGBoost training
- **Main hyperparameters:** `n_estimators=5000`, `max_depth=4`, `learning_rate=0.05`, `subsample=0.8`, `colsample_bytree=0.8`, `early_stopping_rounds=50`
- **Outputs:** saved model and metrics under `artifacts/xgb_*`

### 3.3 Evaluation

I used the same evaluation approach across models.

First, I reported overall validation performance using AUROC and AUPRC. AUPRC was especially important because the outcome was rare in the hospital-wide and non-ICU cohorts.

I also evaluated operational scenarios, including:

- fixed recall targets: 0.40, 0.50, and 0.60
- fixed alert budgets: Top-1000 and Top-3000

The fixed-recall results help answer: “If I want to capture the same percentage of deaths, how many alerts does each model generate?”  
The Top-K results help answer: “If I can only review a fixed number of high-risk admissions, how many true events does the model capture?”

Scenario outputs were saved as `eval_scenarios_latest.csv` under each model artifact directory.

### 3.4 Explainability

For the XGBoost models, I used SHAP mainly as a model sanity check. The goal was not to make causal claims, but to see whether the models were relying on clinically reasonable early features.

For each XGBoost model, I generated:

- global mean absolute SHAP ranking
- top-feature summary plots, such as beeswarm and bar plots

These outputs were saved under the corresponding `artifacts/xgb_*/shap/` directory.

---

## 4. Evaluation Protocol

I evaluated each model on the validation split using both overall performance metrics and threshold-based summaries.

The main metrics were **AUROC** and **AUPRC**. I used AUPRC as an important metric because in-hospital mortality is a rare outcome, especially in the hospital-wide and non-ICU cohorts.

I also looked at two types of threshold scenarios:

- **Fixed recall:** 0.40, 0.50, and 0.60  
  In this setting, I chose the threshold needed to reach each recall target, then compared PPV and the number of alerts generated by each model.

- **Fixed workload:** Top-1000 and Top-3000 highest-risk admissions  
  In this setting, I held the alert budget constant and compared PPV and recall.

For each scenario, I reported the threshold, PPV, recall, specificity, F1 score, total alerts, and the confusion matrix counts: TN, FP, FN, and TP.

I also reported the best-F1 threshold as a reference point. I did not treat this as the final threshold, but it gives a consistent way to compare model performance across versions.



---

## 5. Results

The results below are from the no-demographic/no-administrative runs. In other words, I did not include variables such as `gender`, `race`, `language`, `insurance`, `admission_type`, or `admission_location`. The goal was to keep the main comparison focused on early clinical information.

### 5.1 Hospital-wide validation performance

I first compared the hospital-wide models from V1 to V4. V1–V3 show the effect of expanding the clinical feature set step by step. V4 adds vital-sign summaries, but I interpret it separately because the vital coverage check showed that these features were mostly available only for ICU records.

| Model | Feature set | Cohort        | Valid N | Valid prevalence | AUROC | AUPRC |
|:------|:------------|:--------------|--------:|-----------------:|------:|------:|
| Logit | V1          | Hospital-wide | 291,856 |            0.021 | 0.778 | 0.162 |
| Logit | V2          | Hospital-wide | 291,856 |            0.021 | 0.858 | 0.186 |
| Logit | V3          | Hospital-wide | 291,856 |            0.021 | 0.894 | 0.244 |
| Logit | V4          | Hospital-wide | 291,856 |            0.021 | 0.907 | 0.287 |
| XGB   | V1          | Hospital-wide | 291,856 |            0.021 | 0.842 | 0.211 |
| XGB   | V2          | Hospital-wide | 291,856 |            0.021 | 0.879 | 0.254 |
| XGB   | V3          | Hospital-wide | 291,856 |            0.021 | 0.903 | 0.302 |
| XGB   | V4          | Hospital-wide | 291,856 |            0.021 | 0.926 | 0.385 |

Across the hospital-wide models, performance improved as more early clinical information was added. V2 improved over V1 after adding a broader lab panel and lab missingness flags. V3 improved further after adding early medication/procedure signals and chronic diagnosis groups. V4 had the strongest hospital-wide validation performance after adding vital-sign summaries.

However, I do not treat V4 as the final hospital-wide model. The coverage check showed that these vital-sign features were highly unbalance across care settings: they were mostly available for ICU records and essentially unavailable for non-ICU admissions. Because of that, I used V4 as a feasibility step that motivated the separate ICU and non-ICU models.

### 5.2 Care-setting-specific validation performance

I then evaluated the care-setting-specific models. V5 focuses on hospital admissions with at least one ICU stay and uses ICU vital-sign summaries from the first ICU stay. V6 focuses on non-ICU admissions and does not include ICU vital-sign features.

| Model | Feature set | Cohort   | Valid N | Valid prevalence | AUROC | AUPRC |
|:------|:------------|:---------|--------:|-----------------:|------:|------:|
| Logit | V5          | ICU-only |  44,757 |            0.110 | 0.824 | 0.414 |
| XGB   | V5          | ICU-only |  44,757 |            0.110 | 0.869 | 0.535 |
| Logit | V6          | Non-ICU  | 247,099 |            0.005 | 0.883 | 0.056 |
| XGB   | V6          | Non-ICU  | 247,099 |            0.005 | 0.890 | 0.075 |

The ICU-only model had a much higher outcome prevalence than the non-ICU model, so I interpret V5 and V6 separately rather than as a direct head-to-head comparison. In the ICU cohort, XGBoost performed better than logistic regression, with an AUPRC of **0.535**. This suggests that the model was better at ranking ICU patients by mortality risk, especially because ICU patients had more vital-sign information available. In the non-ICU cohort, the AUPRC was much lower, but this is expected because the outcome prevalence was only about **0.5%**.

### 5.3 Operational threshold scenarios

In addition to AUROC and AUPRC, I also compared the models under threshold-based scenarios. This helps translate model scores into a more practical question: if the model is used to flag high-risk admissions, how many alerts would it generate and how many of those alerts would be true events?

The scenario outputs were generated by `ml/320_eval_scenarios.py`. For each model directory, the script saves an `eval_scenarios_latest.csv` file.

I focused on two types of scenarios:

- **Fixed recall:** choose the threshold needed to reach a target recall, then compare PPV and number of alerts.
- **Fixed workload:** keep the number of alerts fixed and compare PPV and recall.

In the main report, I show the fixed-recall 0.50 and Top-1000 results as representative examples. The other scenario outputs were kept in the saved evaluation files.

#### Fixed recall = 0.50: hospital-wide models

At fixed recall = 0.50, each model captures about half of the in-hospital deaths in the validation dataset. The main comparison is how many alerts are needed to reach that recall, and how many of those alerts are true positives.

| Model | Feature set | Cohort        | Threshold |   PPV | Recall |  Spec | Alerts |
|:------|:------------|:--------------|----------:|------:|-------:|------:|-------:|
| Logit | V1          | Hospital-wide |     0.619 | 0.068 |  0.500 | 0.852 | 45,496 |
| Logit | V2          | Hospital-wide |     0.737 | 0.140 |  0.500 | 0.934 | 22,092 |
| Logit | V3          | Hospital-wide |     0.821 | 0.205 |  0.500 | 0.958 | 15,076 |
| Logit | V4          | Hospital-wide |     0.866 | 0.248 |  0.500 | 0.967 | 12,506 |
| XGB   | V1          | Hospital-wide |     0.684 | 0.126 |  0.500 | 0.925 | 24,639 |
| XGB   | V2          | Hospital-wide |     0.752 | 0.174 |  0.500 | 0.948 | 17,815 |
| XGB   | V3          | Hospital-wide |     0.813 | 0.249 |  0.500 | 0.967 | 12,460 |
| XGB   | V4          | Hospital-wide |     0.835 | 0.316 |  0.500 | 0.977 |  9,789 |

At the same recall, later feature sets produced more efficient alerts. For example, from V1 to V3, the XGBoost model increased PPV from **0.126** to **0.249**, while reducing alerts from **24,639** to **12,460**. V4 improved further, reaching a PPV of **0.316** with **9,789** alerts.

However, as noted earlier, V4 should be interpreted as a feasibility check rather than the final hospital-wide model, because its vital-sign features were mostly available for ICU admissions.

#### Fixed recall = 0.50: care-setting-specific models

I also evaluated the ICU-only and non-ICU models under the same fixed-recall setting. These results should be interpreted within each care setting, because the baseline mortality risk is very different between ICU and non-ICU admissions.

| Model | Feature set | Cohort   | Threshold |   PPV | Recall |  Spec | Alerts |
|:------|:------------|:---------|----------:|------:|-------:|------:|-------:|
| Logit | V5          | ICU-only |     0.679 | 0.376 |  0.500 | 0.897 |  6,573 |
| XGB   | V5          | ICU-only |     0.703 | 0.493 |  0.500 | 0.936 |  5,009 |
| Logit | V6          | Non-ICU  |     0.783 | 0.035 |  0.501 | 0.930 | 17,913 |
| XGB   | V6          | Non-ICU  |     0.751 | 0.044 |  0.500 | 0.945 | 14,245 |

In the ICU cohort, XGBoost reached a PPV of **0.493** at 50% recall, meaning that about half of the flagged ICU admissions were true in-hospital deaths. In the non-ICU cohort, PPV was much lower because death was much rarer, but XGBoost still generated fewer alerts than logistic regression at roughly the same recall.

#### Fixed workload = Top-1000 alerts: hospital-wide models

The Top-1000 scenario asks a different question: if I can only review the 1,000 highest-risk admissions, how many true deaths are captured?

| Model | Feature set | Cohort        | Threshold |   PPV | Recall |  Spec | Alerts |
|:------|:------------|:--------------|----------:|------:|-------:|------:|-------:|
| Logit | V1          | Hospital-wide |     0.981 | 0.530 |  0.086 | 0.998 |  1,000 |
| Logit | V2          | Hospital-wide |     0.992 | 0.461 |  0.074 | 0.998 |  1,000 |
| Logit | V3          | Hospital-wide |     0.996 | 0.532 |  0.086 | 0.998 |  1,000 |
| Logit | V4          | Hospital-wide |     0.997 | 0.605 |  0.098 | 0.999 |  1,000 |
| XGB   | V1          | Hospital-wide |     0.963 | 0.566 |  0.091 | 0.998 |  1,000 |
| XGB   | V2          | Hospital-wide |     0.972 | 0.601 |  0.097 | 0.999 |  1,000 |
| XGB   | V3          | Hospital-wide |     0.977 | 0.627 |  0.101 | 0.999 |  1,000 |
| XGB   | V4          | Hospital-wide |     0.981 | 0.770 |  0.124 | 0.999 |  1,000 |

Under a fixed alert budget, XGBoost generally produced a cleaner high-risk list than logistic regression. XGB V3 captured more true deaths than earlier XGB versions, and XGB V4 had the strongest Top-1000 performance. 

For logistic regression, Top-K performance was not strictly monotonic. For example, V2 had better overall AUROC/AUPRC than V1, but lower Top-1000 PPV. This can happen because Top-K focuses only on the extreme high-risk tail, but AUROC and AUPRC summarize performance over a broader range of thresholds.

#### Fixed workload = Top-1000 alerts: care-setting-specific models

| Model | Feature set | Cohort   | Threshold |   PPV | Recall |  Spec | Alerts |
|:------|:------------|:---------|----------:|------:|-------:|------:|-------:|
| Logit | V5          | ICU-only |     0.938 | 0.665 |  0.135 | 0.992 |  1,000 |
| XGB   | V5          | ICU-only |     0.931 | 0.841 |  0.170 | 0.996 |  1,000 |
| Logit | V6          | Non-ICU  |     0.979 | 0.106 |  0.084 | 0.996 |  1,000 |
| XGB   | V6          | Non-ICU  |     0.900 | 0.143 |  0.114 | 0.997 |  1,000 |

In the ICU cohort, the Top-1000 XGBoost alerts had a PPV of **0.841**, meaning most of the top-ranked ICU admissions were true in-hospital deaths. In the non-ICU cohort, the Top-1000 PPV was much lower, but this is expected because the event rate was only about 0.5%.

Again, I interpret these results within each care setting because the baseline event rates are very different.


### 5.4 Explainability

I used model explainability mainly as a sanity check. The goal was not to make causal claims, but to check whether the models were relying on reasonable early clinical signals.

For logistic regression, I reviewed the largest coefficients from `coeffs_latest.csv`. Since the continuous lab variables were standardized and the missingness/treatment/procedure features were binary indicators, the coefficients gave me a rough directional readout. A positive coefficient means the feature pushes the prediction toward higher risk, while a negative coefficient means it pushes the prediction toward lower risk.

One thing I paid special attention to was lab missingness. Some missingness flags had strong effects, and the direction was not always intuitive. This makes sense in EHR data because missingness is often related to clinical workflow. For example, if a lab was not ordered in the first 24 hours, that can sometimes suggest the patient appeared less sick early on, rather than the value simply being missing at random.

For XGBoost, I used SHAP values to review global feature importance. I summarized each model using mean absolute SHAP values and saved the outputs under the corresponding `artifacts/xgb_*/shap/` directory:

- `shap_mean_abs_ranking.csv`
- `beeswarm_top20.png`
- `bar_top20.png`

#### Hospital-wide models: V1 to V3

The SHAP rankings supported the feature roadmap from V1 to V3.

In V1, the model mainly used age and the small set of early lab/comorbidity features. The top features included `lactate_24h_first`, `age_at_admit`, `creatinine_24h_first`, `sodium_24h_first`, `potassium_24h_first`, and `charlson_min`.

In V2, missingness became an important signal after I added broader labs and missingness flags. Top features included `age_at_admit`, `lactate_24h_missing`, `wbc_24h_first`, `bun_24h_first`, `lactate_24h_first`, and `platelets_24h_first`. This supported the idea that lab availability itself carries information in EHR data.

In V3, the model still used the V2 lab and missingness signals, but early-care features also became important. Top features included `age_at_admit`, `sedative_analgesic_24h`, `lactate_24h_missing`, `bun_24h_first`, `wbc_24h_first`, `vasopressor_24h`, and `anticoag_antiplatelet_24h`. This was consistent with the performance improvement from V2 to V3, because the added medication/procedure flags helped capture early treatment intensity.

#### ICU-only model: V5

For the ICU-only XGBoost model, the top SHAP features were a mix of age, vital signs, labs, early-care signals, and chronic disease indicators.

The most important features included:

- `age_at_admit`
- `spo2_24h_min`
- `bun_24h_first`
- `sedative_analgesic_24h`
- `hr_24h_max`
- `wbc_24h_first`
- `rr_24h_min`
- `malignancy`
- `temp_24h_max`
- `sbp_24h_min`
- `lactate_24h_first`

This made sense for the ICU model. Compared with the hospital-wide V3 model, the ICU model could use more direct physiologic information from vital signs, such as low oxygen saturation, high heart rate, abnormal respiratory rate, and low systolic blood pressure.

#### Non-ICU model: V6

For the non-ICU XGBoost model, the top features looked different. Since ICU vital signs were not available in this cohort, the model relied more on age, chronic disease burden, labs, lab missingness, and early-care signals.

The most important features included:

- `age_at_admit`
- `malignancy`
- `potassium_24h_missing`
- `bun_24h_first`
- `hemoglobin_24h_first`
- `wbc_24h_first`
- `platelets_24h_first`
- `chloride_24h_first`
- `hypertension`
- `chronic_liver`
- `sedative_analgesic_24h`
- `lactate_24h_first`
- `antibiotic_24h`

This was also reasonable. In the non-ICU cohort, mortality was much rarer, and the model did not have ICU-style vital-sign features. As a result, it relied more on baseline risk, lab patterns, missingness, and signs of early treatment.

Overall, the explainability checks matched the modeling roadmap. V1 was driven mostly by age and early labs, V2 added lab availability signal, V3 added treatment-intensity and chronic disease features, V5 used ICU vital signs in addition to labs and early-care signals, and V6 relied on non-ICU-available information without using ICU vital features.


---

## 6. Error Analysis

This section summarizes the error analysis included in this report and briefly notes the follow-up checks I would run next. I focused the detailed error analysis on the XGBoost models because XGBoost was the stronger model family across the main comparisons. Logistic regression was used mainly as a linear baseline and was reviewed through coefficient inspection.

The error groups were assigned using the reference threshold of 0.5:

- **TP:** predicted death and actual death
- **FP:** predicted death but survived
- **FN:** predicted survival but died
- **TN:** predicted survival and survived

This threshold is used here as a consistent reference point for error review. For potential alerting use, I rely more on the fixed-recall and Top-K scenarios described in Section 5.3.

### 6.1 Current error-analysis outputs

I ran the error analysis for the final V5 and V6 XGB models. 

| Model  | Cohort   | Valid N |    TP |     FP |    FN |      TN | Alerts |   PPV | Recall | Specificity |
|:-------|:---------|--------:|------:|-------:|------:|--------:|-------:|------:|-------:|------------:|
| XGB V5 | ICU-only |  44,757 | 3,544 |  6,712 | 1,395 |  33,106 | 10,256 | 0.346 |  0.718 |       0.831 |
| XGB V6 | Non-ICU  | 247,099 | 1,010 | 45,864 |   245 | 199,980 | 46,874 | 0.022 |  0.805 |       0.813 |

For V5, the validation set had 44,757 ICU admissions. At threshold 0.5, the model generated 10,256 alerts. Among these alerts, 3,544 were true positives and 6,712 were false positives. This gave a recall of 0.718 and a PPV of 0.346.

For V6, the validation set had 247,099 non-ICU admissions. At threshold 0.5, the model generated 46,874 alerts. The recall was high at 0.805, but the PPV was much lower at 0.022 because mortality was very rare in the non-ICU cohort.

### 6.2 V5 ICU-only error patterns

In the V5 ICU-only model, false positives did not look like random low-risk admissions. Compared with true negatives, false positives had higher early-risk signals:

- higher BUN and creatinine
- higher lactate
- higher maximum heart rate
- lower minimum systolic blood pressure
- more frequent vasopressor, antibiotic and sedative/analgesic use
- higher malignancy and chronic liver disease burden

This suggests that many V5 false positives were clinically high-risk ICU patients who survived.

False negatives showed a different pattern. Compared with true positives, false negatives had weaker early ICU severity signals. They had lower lactate, lower BUN, lower creatinine, lower maximum heart rate, higher minimum systolic blood pressure, and fewer early treatment-intensity markers such as vasopressors, sedatives/analgesics, and dialysis.

This suggests that some missed ICU deaths were harder to identify using only the first 24 hours of ICU information, because they did not show the same early shock, respiratory, renal, or treatment-intensity pattern as the true positives.

### 6.3 V6 non-ICU error patterns

In the V6 non-ICU model, false positives were also not random low-risk admissions. Compared with true negatives, false positives were older and had higher BUN, higher creatinine, lower hemoglobin, higher malignancy burden, and more early medication signals such as antibiotics and sedatives/analgesics.

This suggests that the model was often flagging clinically high-risk non-ICU patients who survived.

False negatives were different from true positives. Compared with true positives, false negatives were younger and had less abnormal early labs, including lower BUN, lower creatinine, lower WBC, and lower lactate. They also had fewer early treatment-intensity signals.

One important pattern is that false negatives still had higher chronic disease burden than true negatives, especially chronic liver disease, cerebrovascular disease, and malignancy. This suggests that some missed non-ICU deaths may be related more to underlying disease burden or later hospital course than to strong first-24h acute-care signals.

### 6.4 Remaining follow-up analyses

The current error analysis provides a practical summary of the main failure patterns for the final V5 and V6 XGBoost models. In this report, I focus on comparing false positives, false negatives, true positives and true negatives using the available validation outputs.

More detailed case-level review is left as future work. This would include manually reviewing high-score false positives to distinguish clinically reasonable high-risk survivors from possible systematic artifacts and reviewing false negatives to understand whether missed deaths were related to limited early data, weaker first-24h signals, chronic disease burden, or later hospital events.

Temporal stability is also left for future work. A next step would be to slice performance by `anchor_year` and compare prevalence, AUROC, AUPRC, score distributions, and PPV under fixed alert budgets over time. These checks are beyond the scope of the current report, but they would be important before considering real-world use.
---

## 7. Conclusion

In this project, I built an early in-hospital mortality prediction pipeline using MIMIC-IV data. The goal was to use information available early in the hospital or ICU course while avoiding variables that would only become available later in the hospitalization.

I started with a simple hospital-wide baseline and expanded the feature set step by step. From V1 to V3, performance improved after adding broader labs, lab missingness indicators, early medication/procedure signals and chronic disease indicators. This suggested that the added early clinical features provided useful signal.

Across most versions, XGBoost performed better than logistic regression. Logistic regression was still useful as a baseline because it provided a simpler comparison model, while XGBoost captured more non-linear patterns and interactions.

A key finding came from V4. Adding ICU-derived vital-sign summaries improved hospital-wide performance, but the coverage check showed that these features were mostly available for admissions with ICU stays and were missing for most non-ICU admissions. Because of that, I treated V4 as a feasibility check rather than the final hospital-wide model.

This led to the final care-setting-specific approach. For V5, I kept one row per hospital admission but used vital signs from the first ICU stay. For V6, I excluded admissions with any ICU stay and did not include ICU-derived vital-sign features. This made the final model structure more reasonable because each model used features that matched the data available in that care setting.

I interpret the ICU and non-ICU models separately because the two cohorts have very different baseline mortality rates and data availability. The ICU model had higher AUPRC and PPV, while the non-ICU model had lower precision-based performance, which was expected given the much rarer outcome.

Beyond AUROC and AUPRC, I also used fixed-recall and fixed-alert-budget scenarios to understand alert efficiency. The explainability and error-analysis results supported the overall direction of the project: the models relied on reasonable early clinical signals, and many false positives looked like clinically high-risk admissions that survived.

Overall, this project became a full EHR modeling workflow, including cohort construction, feature engineering, model training, validation, scenario evaluation, explainability, and error analysis. The main conclusion is that early clinical information can support useful mortality risk prediction, but the model design needs to respect care-setting-specific data availability. The ICU and non-ICU models therefore provide a better final framework than a single hospital-wide model relying on unevenly available ICU-derived vital signs.

Future work would include manual review of selected false positives and false negatives, subgroup review, and temporal stability checks by anchor_year. These steps are outside the scope of the current report but would be important before considering prospective validation or real-world use.