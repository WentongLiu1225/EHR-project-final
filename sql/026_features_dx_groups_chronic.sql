/*
  Chronic diagnosis group flags.

  This view creates coarse admission-level chronic disease flags from
  diagnoses_icd. These features were added to capture disease burden beyond
  the small Charlson-style summary.
*/

create schema if not exists features;

create or replace view features.dx_groups_chronic as
with dx as (
  select
    hadm_id,
    case
      when icd_version = 9 then 'ICD9'
      else 'ICD10'
    end as ver,
    icd_code
  from mimiciv_hosp.diagnoses_icd
),

grp as (
  select
    hadm_id,

    -- COPD / chronic pulmonary disease
    max(case
      when (ver = 'ICD9' and (
              icd_code like '491%'
           or icd_code like '492%'
           or icd_code like '496%'
           ))
        or (ver = 'ICD10' and (
              icd_code like 'J44%'
           or icd_code like 'J43%'
           ))
      then 1 else 0
    end) as COPD,

    -- chronic liver disease / cirrhosis
    max(case
      when (ver = 'ICD9' and icd_code like '571%')
        or (ver = 'ICD10' and (
              icd_code like 'K70%'
           or icd_code like 'K74%'
           ))
      then 1 else 0
    end) as CHRONIC_LIVER,

    -- malignancy, broad grouping
    max(case
      when (ver = 'ICD9' and icd_code between '140' and '239')
        or (ver = 'ICD10' and (
              icd_code like 'C%'
           or icd_code like 'D0%'
           ))
      then 1 else 0
    end) as MALIGNANCY,

    -- cerebrovascular disease / stroke / TIA history
    max(case
      when (ver = 'ICD9' and (
              icd_code like '433%'
           or icd_code like '434%'
           or icd_code like '435%'
           or icd_code like '436%'
           ))
        or (ver = 'ICD10' and (
              icd_code like 'I63%'
           or icd_code like 'I64%'
           or icd_code like 'G45%'
           ))
      then 1 else 0
    end) as CEREBROVASCULAR,

    -- hypertension
    max(case
      when (ver = 'ICD9' and icd_code like '401%')
        or (ver = 'ICD10' and icd_code like 'I10%')
      then 1 else 0
    end) as HYPERTENSION,

    -- coronary artery disease / ischemic heart disease
    max(case
      when (ver = 'ICD9' and (
              icd_code like '410%'
           or icd_code like '411%'
           or icd_code like '414%'
           ))
        or (ver = 'ICD10' and (
              icd_code like 'I21%'
           or icd_code like 'I22%'
           or icd_code like 'I25%'
           ))
      then 1 else 0
    end) as CAD

  from dx
  group by hadm_id
)

select *
from grp;