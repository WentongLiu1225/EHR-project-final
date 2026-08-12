/*
  Minimal Charlson-style comorbidity flags.

  This view uses diagnosis codes to create a few admission-level
  comorbidity flags and a simple summary score for modeling.
*/

create schema if not exists features;

create or replace view features.charlson_flags as
with dx as (
  select
    hadm_id,
    case
      when icd_version = 9 then 'ICD9'
      when icd_version = 10 then 'ICD10'
    end as ver,
    icd_code
  from mimiciv_hosp.diagnoses_icd
  where hadm_id is not null
),

flags as (
  select
    hadm_id,

    -- congestive heart failure
    max(case
      when (ver = 'ICD9' and icd_code like '428%')
        or (ver = 'ICD10' and icd_code like 'I50%')
      then 1 else 0
    end) as CHF,

    -- renal disease, using a simple CKD-based rule
    max(case
      when (ver = 'ICD9' and icd_code between '585' and '5859')
        or (ver = 'ICD10' and icd_code like 'N18%')
      then 1 else 0
    end) as RENAL,

    -- diabetes mellitus, rough grouping
    max(case
      when (ver = 'ICD9' and icd_code like '250%')
        or (ver = 'ICD10' and icd_code like 'E1%')
      then 1 else 0
    end) as DM

  from dx
  group by hadm_id
)

select
  hadm_id, CHF, RENAL, DM,
  (CHF * 1 + RENAL * 2 + DM * 1) as charlson_min
from flags;