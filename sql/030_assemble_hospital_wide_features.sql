/*
  Assemble hospital-wide feature views.

  This file builds V1 through V4 feature views for the hospital-wide
  modeling roadmap.

  V1: core labs + minimal Charlson summary
  V2: extended labs + lab missingness
  V3: adds early meds/procedures and chronic dx groups
  V4: adds first-24h ICU-derived vital summaries as a feasibility check
*/

create schema if not exists features;


-- V1: core hospital-wide baseline
create or replace view features.inhosp_mortality_features as
select
  b.hadm_id,
  b.subject_id,
  b.admittime,
  b.y_inhosp_death,
  b.age_at_admit,

  l.sodium_24h_first,
  l.potassium_24h_first,
  l.creatinine_24h_first,
  l.lactate_24h_first,

  c.charlson_min

from features.inhosp_mortality_base b
left join features.labs_24h l using (hadm_id)
left join features.charlson_flags c using (hadm_id);


-- V2: extended labs and lab missingness flags
create or replace view features.inhosp_mortality_features_v2 as
with base as (
  select * from features.inhosp_mortality_base
),
lab as (
  select * from features.labs_24h_ext
),
charl as (
  select * from features.charlson_flags
)

select
  b.hadm_id,
  b.subject_id,
  b.admittime,
  b.y_inhosp_death,
  b.age_at_admit,

  -- labs, first value within 24h
  l.sodium_24h_first,
  l.potassium_24h_first,
  l.creatinine_24h_first,
  l.lactate_24h_first,
  l.glucose_24h_first,
  l.bun_24h_first,
  l.chloride_24h_first,
  l.bicarbonate_24h_first,
  l.calcium_24h_first,
  l.magnesium_24h_first,
  l.phosphate_24h_first,
  l.wbc_24h_first,
  l.hemoglobin_24h_first,
  l.platelets_24h_first,

  -- lab missingness flags, 1 = missing
  (l.sodium_24h_first is null)::int as sodium_24h_missing,
  (l.potassium_24h_first is null)::int as potassium_24h_missing,
  (l.creatinine_24h_first is null)::int as creatinine_24h_missing,
  (l.lactate_24h_first is null)::int as lactate_24h_missing,
  (l.glucose_24h_first is null)::int as glucose_24h_missing,
  (l.bun_24h_first is null)::int as bun_24h_missing,
  (l.chloride_24h_first is null)::int as chloride_24h_missing,
  (l.bicarbonate_24h_first is null)::int as bicarbonate_24h_missing,
  (l.calcium_24h_first is null)::int as calcium_24h_missing,
  (l.magnesium_24h_first is null)::int as magnesium_24h_missing,
  (l.phosphate_24h_first is null)::int as phosphate_24h_missing,
  (l.wbc_24h_first is null)::int as wbc_24h_missing,
  (l.hemoglobin_24h_first is null)::int as hemoglobin_24h_missing,
  (l.platelets_24h_first is null)::int as platelets_24h_missing,

  c.charlson_min

from base b
left join lab l using (hadm_id)
left join charl c using (hadm_id);


-- V3: early-care signals and chronic diagnosis groups
create or replace view features.inhosp_mortality_features_v3 as
with base as (
  select * from features.inhosp_mortality_base
),
lab as (
  select * from features.labs_24h_ext
),
charl as (
  select * from features.charlson_flags
),
med as (
  select * from features.meds_24h
),
prc as (
  select * from features.procs_24h
),
dxg as (
  select * from features.dx_groups_chronic
)

select
  b.hadm_id,
  b.subject_id,
  b.admittime,
  b.y_inhosp_death,
  b.age_at_admit,

  -- labs, first value within 24h
  l.sodium_24h_first,
  l.potassium_24h_first,
  l.creatinine_24h_first,
  l.lactate_24h_first,
  l.glucose_24h_first,
  l.bun_24h_first,
  l.chloride_24h_first,
  l.bicarbonate_24h_first,
  l.calcium_24h_first,
  l.magnesium_24h_first,
  l.phosphate_24h_first,
  l.wbc_24h_first,
  l.hemoglobin_24h_first,
  l.platelets_24h_first,

  -- lab missingness flags, 1 = missing
  (l.sodium_24h_first is null)::int as sodium_24h_missing,
  (l.potassium_24h_first is null)::int as potassium_24h_missing,
  (l.creatinine_24h_first is null)::int as creatinine_24h_missing,
  (l.lactate_24h_first is null)::int as lactate_24h_missing,
  (l.glucose_24h_first is null)::int as glucose_24h_missing,
  (l.bun_24h_first is null)::int as bun_24h_missing,
  (l.chloride_24h_first is null)::int as chloride_24h_missing,
  (l.bicarbonate_24h_first is null)::int as bicarbonate_24h_missing,
  (l.calcium_24h_first is null)::int as calcium_24h_missing,
  (l.magnesium_24h_first is null)::int as magnesium_24h_missing,
  (l.phosphate_24h_first is null)::int as phosphate_24h_missing,
  (l.wbc_24h_first is null)::int as wbc_24h_missing,
  (l.hemoglobin_24h_first is null)::int as hemoglobin_24h_missing,
  (l.platelets_24h_first is null)::int as platelets_24h_missing,

  c.charlson_min,

  -- early medication flags
  m.vasopressor_24h,
  m.antibiotic_24h,
  m.insulin_24h,
  m.diuretic_24h,
  m.anticoag_antiplatelet_24h,
  m.sedative_analgesic_24h,

  -- early ICU procedure flags
  p.airway_intubation_24h,
  p.central_line_24h,
  p.arterial_line_24h,
  p.dialysis_24h,
  p.chest_tube_24h,

  -- chronic diagnosis groups
  dg.copd,
  dg.chronic_liver,
  dg.malignancy,
  dg.cerebrovascular,
  dg.hypertension,
  dg.cad

from base b
left join lab l using (hadm_id)
left join charl c using (hadm_id)
left join med m using (hadm_id)
left join prc p using (hadm_id)
left join dxg dg using (hadm_id);


-- V4: hospital-wide vital-sign feasibility check
create or replace view features.inhosp_mortality_features_v4 as
with v3 as (
  select * from features.inhosp_mortality_features_v3
),
vit as (
  select * from features.vitals_24h
)

select
  v3.*,

  vit.hr_24h_first,
  vit.hr_24h_min,
  vit.hr_24h_max,

  vit.rr_24h_first,
  vit.rr_24h_min,
  vit.rr_24h_max,

  vit.sbp_24h_first,
  vit.sbp_24h_min,
  vit.sbp_24h_max,

  vit.dbp_24h_first,
  vit.dbp_24h_min,
  vit.dbp_24h_max,

  vit.spo2_24h_first,
  vit.spo2_24h_min,
  vit.spo2_24h_max,

  vit.temp_24h_first,
  vit.temp_24h_min,
  vit.temp_24h_max,

  -- vital missingness flags, 1 = no first value observed
  (vit.hr_24h_first is null)::int as hr_24h_missing,
  (vit.rr_24h_first is null)::int as rr_24h_missing,
  (vit.sbp_24h_first is null)::int as sbp_24h_missing,
  (vit.dbp_24h_first is null)::int as dbp_24h_missing,
  (vit.spo2_24h_first is null)::int as spo2_24h_missing,
  (vit.temp_24h_first is null)::int as temp_24h_missing

from v3
left join vit using (hadm_id);