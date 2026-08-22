/*
  Base cohort for in-hospital mortality modeling.
  One row per hospital admission, adult admissions only.
*/

create schema if not exists features;

create or replace view features.inhosp_mortality_base as
with base as (
  select
    a.hadm_id,
    a.subject_id,
    a.admittime,

    case when a.hospital_expire_flag = 1 then 1 else 0 end as y_inhosp_death,

    -- age estimate from MIMIC anchor fields
    round(
      (p.anchor_age + extract(year from a.admittime) - p.anchor_year)::numeric,
      1
    ) as age_at_admit,

    -- kept for reference; not used in main models
    p.gender,
    a.admission_type,
    a.admission_location,
    a.insurance,
    a.race,
    a.language

  from mimiciv_hosp.admissions a
  join mimiciv_hosp.patients p using (subject_id)
)
select *
from base
where age_at_admit >= 18;
