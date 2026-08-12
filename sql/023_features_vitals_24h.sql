/*
  First-24h vital sign features.

  This view summarizes ICU-derived vital signs during the first 24 hours
  after hospital admission. It was used for the V4 hospital-wide vitals
  feasibility check.

  admittime <= charttime < admittime + 24 hours
*/

create schema if not exists features;

drop view if exists features.vitals_24h cascade;

create view features.vitals_24h as
with base as (
  select
    hadm_id,
    subject_id,
    admittime
  from features.inhosp_mortality_base
),

raw_vitals as (
  select
    b.hadm_id,
    b.subject_id,
    ce.charttime,
    ce.itemid,
    ce.valuenum,

    case
      when ce.itemid = 220045 then 'hr'
      when ce.itemid = 220210 then 'rr'
      when ce.itemid in (220050, 220179) then 'sbp'
      when ce.itemid in (220051, 220180) then 'dbp'
      when ce.itemid = 220277 then 'spo2'
      when ce.itemid = 223762 then 'temp_c'
      when ce.itemid = 223761 then 'temp_f'
      else null
    end as vital_type

  from base b
  join staging.chartevents_vitals_subset ce
    on ce.hadm_id = b.hadm_id
   and ce.subject_id = b.subject_id
  where ce.charttime >= b.admittime
    and ce.charttime <  b.admittime + interval '24 hours'
    and ce.valuenum is not null
),

clean_vitals as (
  select
    hadm_id,
    subject_id,
    charttime,

    case
      when vital_type in ('temp_c', 'temp_f') then 'temp'
      else vital_type
    end as vital_name,

    case
      when vital_type = 'temp_f' then (valuenum - 32.0) * 5.0 / 9.0
      else valuenum
    end as vital_value

  from raw_vitals
  where vital_type is not null
),

filtered_vitals as (
  select *
  from clean_vitals
  where
       (vital_name = 'hr'   and vital_value between 20 and 300)
    or (vital_name = 'rr'   and vital_value between 2  and 80)
    or (vital_name = 'sbp'  and vital_value between 30 and 300)
    or (vital_name = 'dbp'  and vital_value between 10 and 200)
    or (vital_name = 'spo2' and vital_value between 30 and 100)
    or (vital_name = 'temp' and vital_value between 25 and 45)
),

first_rows as (
  select
    hadm_id,
    vital_name,
    vital_value,

    row_number() over (
      partition by hadm_id, vital_name
      order by charttime
    ) as rn

  from filtered_vitals
),

first_pivot as (
  select
    hadm_id,

    max(case when vital_name = 'hr'   and rn = 1 then vital_value end) as hr_24h_first,
    max(case when vital_name = 'rr'   and rn = 1 then vital_value end) as rr_24h_first,
    max(case when vital_name = 'sbp'  and rn = 1 then vital_value end) as sbp_24h_first,
    max(case when vital_name = 'dbp'  and rn = 1 then vital_value end) as dbp_24h_first,
    max(case when vital_name = 'spo2' and rn = 1 then vital_value end) as spo2_24h_first,
    max(case when vital_name = 'temp' and rn = 1 then vital_value end) as temp_24h_first

  from first_rows
  group by hadm_id
),

agg_pivot as (
  select
    hadm_id,

    min(case when vital_name = 'hr' then vital_value end) as hr_24h_min,
    max(case when vital_name = 'hr' then vital_value end) as hr_24h_max,

    min(case when vital_name = 'rr' then vital_value end) as rr_24h_min,
    max(case when vital_name = 'rr' then vital_value end) as rr_24h_max,

    min(case when vital_name = 'sbp' then vital_value end) as sbp_24h_min,
    max(case when vital_name = 'sbp' then vital_value end) as sbp_24h_max,

    min(case when vital_name = 'dbp' then vital_value end) as dbp_24h_min,
    max(case when vital_name = 'dbp' then vital_value end) as dbp_24h_max,

    min(case when vital_name = 'spo2' then vital_value end) as spo2_24h_min,
    max(case when vital_name = 'spo2' then vital_value end) as spo2_24h_max,

    min(case when vital_name = 'temp' then vital_value end) as temp_24h_min,
    max(case when vital_name = 'temp' then vital_value end) as temp_24h_max

  from filtered_vitals
  group by hadm_id
)

select
  b.hadm_id,

  f.hr_24h_first,
  a.hr_24h_min,
  a.hr_24h_max,

  f.rr_24h_first,
  a.rr_24h_min,
  a.rr_24h_max,

  f.sbp_24h_first,
  a.sbp_24h_min,
  a.sbp_24h_max,

  f.dbp_24h_first,
  a.dbp_24h_min,
  a.dbp_24h_max,

  f.spo2_24h_first,
  a.spo2_24h_min,
  a.spo2_24h_max,

  f.temp_24h_first,
  a.temp_24h_min,
  a.temp_24h_max

from base b
left join first_pivot f using (hadm_id)
left join agg_pivot a using (hadm_id);