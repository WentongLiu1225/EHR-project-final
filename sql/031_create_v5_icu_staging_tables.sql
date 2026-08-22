/*
  V5 ICU staging tables.

  This script creates the ICU cohort used for the V5 model.
  For admissions with multiple ICU stays, only the first ICU stay is kept.

  It also creates the empty staging table used to load first-24h ICU vital
  features. The vital feature rows are generated locally from raw chartevents
  and are not included in this repository.
*/

create schema if not exists staging;

drop table if exists staging.v3_icu_cohort;
drop table if exists staging.v3_icu_vitals_24h_features;


-- Keep the first ICU stay per hospital admission
create table staging.v3_icu_cohort as
with first_icu_stay as (
  select
    i.*,
    row_number() over (
      partition by i.hadm_id
      order by i.intime asc, i.stay_id asc
    ) as rn
  from mimiciv_icu.icustays i
  where i.hadm_id is not null
    and i.stay_id is not null
    and i.intime is not null
)

select
  v3.*,
  i.stay_id,
  i.intime,
  i.outtime,
  i.first_careunit,
  i.last_careunit
from features.inhosp_mortality_features_v3 v3
join first_icu_stay i
  on v3.hadm_id = i.hadm_id
where i.rn = 1;


create index idx_v3_icu_cohort_hadm_id
  on staging.v3_icu_cohort (hadm_id);

create index idx_v3_icu_cohort_stay_id
  on staging.v3_icu_cohort (stay_id);

create index idx_v3_icu_cohort_intime
  on staging.v3_icu_cohort (intime);

-- Safety checks: fail if the table is no longer one row per hadm_id/stay_id
create unique index idx_v3_icu_cohort_unique_hadm_id
  on staging.v3_icu_cohort (hadm_id);

create unique index idx_v3_icu_cohort_unique_stay_id
  on staging.v3_icu_cohort (stay_id);


-- Empty table populated later by local ICU vital feature extraction
create table staging.v3_icu_vitals_24h_features (
  hadm_id            integer,
  stay_id            integer,
  intime             timestamp,

  hr_24h_first       double precision,
  hr_24h_min         double precision,
  hr_24h_max         double precision,

  rr_24h_first       double precision,
  rr_24h_min         double precision,
  rr_24h_max         double precision,

  sbp_24h_first      double precision,
  sbp_24h_min        double precision,
  sbp_24h_max        double precision,

  dbp_24h_first      double precision,
  dbp_24h_min        double precision,
  dbp_24h_max        double precision,

  spo2_24h_first     double precision,
  spo2_24h_min       double precision,
  spo2_24h_max       double precision,

  temp_24h_first     double precision,
  temp_24h_min       double precision,
  temp_24h_max       double precision,

  hr_24h_missing     integer,
  rr_24h_missing     integer,
  sbp_24h_missing    integer,
  dbp_24h_missing    integer,
  spo2_24h_missing   integer,
  temp_24h_missing   integer
);

create index idx_v3_icu_vitals_24h_features_hadm_id
  on staging.v3_icu_vitals_24h_features (hadm_id);

create index idx_v3_icu_vitals_24h_features_stay_id
  on staging.v3_icu_vitals_24h_features (stay_id);