/*
  First-24h medication group flags.

  This view creates admission-level medication flags based on prescriptions
  started within the first 24 hours after hospital admission.
*/

create schema if not exists features;

create or replace view features.meds_24h as
with rx as (
  select
    a.hadm_id,
    lower(coalesce(pr.drug, '')) as txt

  from mimiciv_hosp.admissions a
  join mimiciv_hosp.prescriptions pr
    on pr.hadm_id = a.hadm_id
   and pr.starttime is not null
   and pr.starttime >= a.admittime
   and pr.starttime <  a.admittime + interval '24 hours'
),

grp as (
  select
    hadm_id,

    max((txt ~ '(norepi|norepinephrine|epinephrine|vasopressin|dopamine|phenylephrine|levophed)')::int) as vasopressor_24h,
    max((txt ~ '(vancomycin|piperacillin|tazobactam|meropenem|cefepime|ceftriaxone|zosyn|levofloxacin|ciprofloxacin|linezolid|metronidazole)')::int) as antibiotic_24h,
    max((txt ~ '(insulin)')::int) as insulin_24h,
    max((txt ~ '(furosemide|lasix|bumetanide|torsemide|hydrochlorothiazide)')::int) as diuretic_24h,
    max((txt ~ '(heparin|enoxaparin|warfarin|apixaban|rivaroxaban|clopidogrel|aspirin)')::int) as anticoag_antiplatelet_24h,
    max((txt ~ '(propofol|midazolam|fentanyl|dexmedetomidine)')::int) as sedative_analgesic_24h

  from rx
  group by hadm_id
)

select *
from grp;