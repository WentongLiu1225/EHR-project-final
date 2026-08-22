/*
  First-24h lab features.

  This file builds two lab views:
  - features.labs_24h: core lab panel used in V1
  - features.labs_24h_ext: extended lab panel used in V2 and later versions

  Both views use the first available lab value within 24 hours after admission:
  admittime <= charttime < admittime + 24 hours
*/

create schema if not exists features;


-- Core lab panel for V1
create or replace view features.labs_24h as
with labs as (
  select
    a.hadm_id,
    le.itemid,
    le.valuenum,
    le.charttime,
    row_number() over (
      partition by a.hadm_id, le.itemid
      order by le.charttime
    ) as rn
  from mimiciv_hosp.admissions a
  join mimiciv_hosp.labevents le
    on le.hadm_id = a.hadm_id
   and le.charttime >= a.admittime
   and le.charttime <  a.admittime + interval '24 hours'
  where le.valuenum is not null
    and le.itemid in (
      50983,  -- sodium
      50971,  -- potassium
      50912,  -- creatinine
      50813   -- lactate
    )
)

select
  hadm_id,
  max(case when itemid = 50983 then valuenum end) as sodium_24h_first,
  max(case when itemid = 50971 then valuenum end) as potassium_24h_first,
  max(case when itemid = 50912 then valuenum end) as creatinine_24h_first,
  max(case when itemid = 50813 then valuenum end) as lactate_24h_first
from labs
where rn = 1
group by hadm_id;


-- Extended lab panel for V2 and later versions
create or replace view features.labs_24h_ext as
with labs as (
  select
    a.hadm_id,
    le.itemid,
    le.valuenum,
    le.charttime,
    row_number() over (
      partition by a.hadm_id, le.itemid
      order by le.charttime
    ) as rn
  from mimiciv_hosp.admissions a
  join mimiciv_hosp.labevents le
    on le.hadm_id = a.hadm_id
   and le.charttime >= a.admittime
   and le.charttime <  a.admittime + interval '24 hours'
  where le.valuenum is not null
    and le.itemid in (
      -- core labs
      50983,  -- sodium
      50971,  -- potassium
      50912,  -- creatinine
      50813,  -- lactate

      -- chemistry / renal
      50931,  -- glucose
      51006,  -- BUN
      50902,  -- chloride
      50882,  -- bicarbonate

      -- electrolytes
      50893,  -- calcium
      50960,  -- magnesium
      50970,  -- phosphate

      -- CBC
      51301,  -- WBC
      51222,  -- hemoglobin
      51265   -- platelets
    )
)

select
  hadm_id,

  -- core labs
  max(case when itemid = 50983 then valuenum end) as sodium_24h_first,
  max(case when itemid = 50971 then valuenum end) as potassium_24h_first,
  max(case when itemid = 50912 then valuenum end) as creatinine_24h_first,
  max(case when itemid = 50813 then valuenum end) as lactate_24h_first,

  -- extended labs
  max(case when itemid = 50931 then valuenum end) as glucose_24h_first,
  max(case when itemid = 51006 then valuenum end) as bun_24h_first,
  max(case when itemid = 50902 then valuenum end) as chloride_24h_first,
  max(case when itemid = 50882 then valuenum end) as bicarbonate_24h_first,
  max(case when itemid = 50893 then valuenum end) as calcium_24h_first,
  max(case when itemid = 50960 then valuenum end) as magnesium_24h_first,
  max(case when itemid = 50970 then valuenum end) as phosphate_24h_first,
  max(case when itemid = 51301 then valuenum end) as wbc_24h_first,
  max(case when itemid = 51222 then valuenum end) as hemoglobin_24h_first,
  max(case when itemid = 51265 then valuenum end) as platelets_24h_first
from labs
where rn = 1
group by hadm_id;
