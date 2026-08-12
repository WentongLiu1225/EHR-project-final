/*
  First-24h ICU procedure flags.

  This view creates admission-level flags for selected ICU procedures
  or interventions recorded within the first 24 hours after admission.
*/

create schema if not exists features;

create or replace view features.procs_24h as
with pe as (
  select
    a.hadm_id,
    di.label,
    p.starttime

  from mimiciv_hosp.admissions a
  join mimiciv_icu.icustays i
    on i.hadm_id = a.hadm_id
  join mimiciv_icu.procedureevents p
    on p.stay_id = i.stay_id
  join mimiciv_icu.d_items di
    on di.itemid = p.itemid

  where p.starttime is not null
    and p.starttime >= a.admittime
    and p.starttime <  a.admittime + interval '24 hours'
),

tok as (
  select
    hadm_id,
    lower(label) as lbl
  from pe
),

grp as (
  select
    hadm_id,

    max((lbl ~ '(intubat|endotrache|tracheostom)')::int) as airway_intubation_24h,
    max((lbl ~ '(central.*line|cvc|central venous|subclavian|internal jugular|ij line)')::int) as central_line_24h,
    max((lbl ~ '(arterial.*line|a[- ]?line)')::int) as arterial_line_24h,
    max((lbl ~ '(dialysis|hemodialysis|cvvh|cvvhd|cvvhdf|crrt)')::int) as dialysis_24h,
    max((lbl ~ '(chest.*tube|thoracostom)')::int) as chest_tube_24h

  from tok
  group by hadm_id
)

select
  hadm_id, airway_intubation_24h,
  central_line_24h,
  arterial_line_24h,
  dialysis_24h,
  chest_tube_24h
from grp;
