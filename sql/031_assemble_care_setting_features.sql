/*
  Assemble care-setting-specific feature tables.

  V5: ICU-only feature table with first ICU stay vital features.
  V6: Non-ICU feature table, based on V3 features and excluding any ICU stay.

  These are materialized as tables because they are reused downstream for
  training, evaluation, and error analysis.
*/

create schema if not exists features;


-- V5: ICU-only admission-level feature table
drop table if exists features.inhosp_mortality_features_v5_icu;

create table features.inhosp_mortality_features_v5_icu as
select
  c.*,

  v.hr_24h_first,
  v.hr_24h_min,
  v.hr_24h_max,

  v.rr_24h_first,
  v.rr_24h_min,
  v.rr_24h_max,

  v.sbp_24h_first,
  v.sbp_24h_min,
  v.sbp_24h_max,

  v.dbp_24h_first,
  v.dbp_24h_min,
  v.dbp_24h_max,

  v.spo2_24h_first,
  v.spo2_24h_min,
  v.spo2_24h_max,

  v.temp_24h_first,
  v.temp_24h_min,
  v.temp_24h_max,

  v.hr_24h_missing,
  v.rr_24h_missing,
  v.sbp_24h_missing,
  v.dbp_24h_missing,
  v.spo2_24h_missing,
  v.temp_24h_missing

from staging.v3_icu_cohort c
left join staging.v3_icu_vitals_24h_features v
  on c.stay_id = v.stay_id
 and c.hadm_id = v.hadm_id;

create index idx_inhosp_mortality_features_v5_icu_hadm_id
  on features.inhosp_mortality_features_v5_icu (hadm_id);

create index idx_inhosp_mortality_features_v5_icu_stay_id
  on features.inhosp_mortality_features_v5_icu (stay_id);

create unique index idx_inhosp_mortality_features_v5_icu_unique_hadm_id
  on features.inhosp_mortality_features_v5_icu (hadm_id);

analyze features.inhosp_mortality_features_v5_icu;


-- V6: non-ICU admission-level feature table
drop table if exists features.inhosp_mortality_features_v6_nonicu;

create table features.inhosp_mortality_features_v6_nonicu as
select
  v3.*
from features.inhosp_mortality_features_v3 v3
where not exists (
  select 1
  from mimiciv_icu.icustays i
  where i.hadm_id = v3.hadm_id
);

create index idx_inhosp_mortality_features_v6_nonicu_hadm_id
  on features.inhosp_mortality_features_v6_nonicu (hadm_id);

analyze features.inhosp_mortality_features_v6_nonicu;