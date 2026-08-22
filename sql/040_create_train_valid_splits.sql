/*
  Train / validation split tables.

  V1 to V4 use the same time-based rule from patient anchor_year:
    anchor_year < 2150  -> train
    anchor_year >= 2150 -> valid

  V5 and V6 reuse the V4 split assignment at the hadm_id level.
*/

create schema if not exists features;


-- V1 split
create or replace view features.split as
select
  f.*,
  case
    when p.anchor_year < 2150 then 'train' else 'valid'
  end as split
from features.inhosp_mortality_features f
join mimiciv_hosp.patients p
  on p.subject_id = f.subject_id;


-- V2 split
create or replace view features.split_v2 as
select
  f2.*,
  case
    when p.anchor_year < 2150 then 'train' else 'valid'
  end as split
from features.inhosp_mortality_features_v2 f2
join mimiciv_hosp.patients p
  on p.subject_id = f2.subject_id;


-- V3 split
create or replace view features.split_v3 as
select
  f3.*,
  case
    when p.anchor_year < 2150 then 'train' else 'valid'
  end as split
from features.inhosp_mortality_features_v3 f3
join mimiciv_hosp.patients p
  on p.subject_id = f3.subject_id;


-- V4 split
create or replace view features.split_v4 as
select
  f4.*,
  case
    when p.anchor_year < 2150 then 'train' else 'valid'
  end as split
from features.inhosp_mortality_features_v4 f4
join mimiciv_hosp.patients p
  on p.subject_id = f4.subject_id;


-- V5 ICU split table
drop table if exists features.split_v5_icu;

create table features.split_v5_icu as
select
  f.*,
  s.split
from features.inhosp_mortality_features_v5_icu f
inner join features.split_v4 s
  on f.hadm_id = s.hadm_id;

create index idx_split_v5_icu_hadm_id
  on features.split_v5_icu (hadm_id);

create index idx_split_v5_icu_stay_id
  on features.split_v5_icu (stay_id);

create index idx_split_v5_icu_split
  on features.split_v5_icu (split);

analyze features.split_v5_icu;


-- V6 non-ICU split table
drop table if exists features.split_v6_nonicu;

create table features.split_v6_nonicu as
select
  f.*,
  s.split
from features.inhosp_mortality_features_v6_nonicu f
inner join features.split_v4 s
  on f.hadm_id = s.hadm_id;

create index idx_split_v6_nonicu_hadm_id
  on features.split_v6_nonicu (hadm_id);

create index idx_split_v6_nonicu_split
  on features.split_v6_nonicu (split);

analyze features.split_v6_nonicu;