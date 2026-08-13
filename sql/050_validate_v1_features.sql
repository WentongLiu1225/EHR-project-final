\pset pager off

/*
  Validate V1 feature set and split.

  This script is a quick QC pass after building:
  - features.inhosp_mortality_base
  - features.labs_24h
  - features.charlson_flags
  - features.inhosp_mortality_features
  - features.split

  It checks object existence, row counts, hadm_id uniqueness,
  outcome values, split distribution, and basic missingness.
*/


-- connection info, just to make sure I am checking the right DB/session
select
  current_database() as db,
  current_user as usr,
  inet_server_addr() as server_addr,
  inet_server_port() as server_port;


-- stop early if any required object is missing
do $$
declare
  missing text := '';
begin
  if to_regclass('features.inhosp_mortality_base') is null then
    missing := missing || E'\n- features.inhosp_mortality_base';
  end if;

  if to_regclass('features.labs_24h') is null then
    missing := missing || E'\n- features.labs_24h';
  end if;

  if to_regclass('features.charlson_flags') is null then
    missing := missing || E'\n- features.charlson_flags';
  end if;

  if to_regclass('features.inhosp_mortality_features') is null then
    missing := missing || E'\n- features.inhosp_mortality_features';
  end if;

  if to_regclass('features.split') is null then
    missing := missing || E'\n- features.split';
  end if;

  if missing <> '' then
    raise exception 'Missing required objects:%', missing;
  end if;
end $$;


-- print object names so I can quickly see what exists
select
  to_regclass('features.inhosp_mortality_base')     as has_base,
  to_regclass('features.labs_24h')                  as has_labs24h,
  to_regclass('features.charlson_flags')            as has_charlson,
  to_regclass('features.inhosp_mortality_features') as has_features,
  to_regclass('features.split')                     as has_split;


-- basic row counts
with counts as (
  select 'base' as obj, count(*) as n
  from features.inhosp_mortality_base

  union all
  select 'labs_24h', count(*)
  from features.labs_24h

  union all
  select 'charlson_flags', count(*)
  from features.charlson_flags

  union all
  select 'features_assembled', count(*)
  from features.inhosp_mortality_features

  union all
  select 'split', count(*)
  from features.split
)

select *
from counts
order by obj;


-- hard fail if assembled features do not line up with base / split
do $$
declare
  n_base bigint;
  n_feat bigint;
  n_split bigint;
begin
  select count(*) into n_base
  from features.inhosp_mortality_base;

  select count(*) into n_feat
  from features.inhosp_mortality_features;

  select count(*) into n_split
  from features.split;

  if n_feat <> n_base then
    raise exception
      'Row count mismatch: features.inhosp_mortality_features(%) != base(%)',
      n_feat, n_base;
  end if;

  if n_split <> n_feat then
    raise exception
      'Row count mismatch: features.split(%) != features_assembled(%)',
      n_split, n_feat;
  end if;
end $$;


-- key check: row count, distinct hadm_id, null hadm_id
select
  'base' as obj,
  count(*) as n,
  count(distinct hadm_id) as n_distinct_hadm,
  sum((hadm_id is null)::int) as n_null_hadm
from features.inhosp_mortality_base

union all

select
  'features_assembled' as obj,
  count(*) as n,
  count(distinct hadm_id) as n_distinct_hadm,
  sum((hadm_id is null)::int) as n_null_hadm
from features.inhosp_mortality_features

union all

select
  'split' as obj,
  count(*) as n,
  count(distinct hadm_id) as n_distinct_hadm,
  sum((hadm_id is null)::int) as n_null_hadm
from features.split;


-- stop if assembled V1 features duplicated hadm_id
do $$
declare
  dup_n bigint;
begin
  select count(*) into dup_n
  from (
    select hadm_id
    from features.inhosp_mortality_features
    group by hadm_id
    having count(*) > 1
  ) t;

  if dup_n > 0 then
    raise exception
      'Detected duplicate hadm_id in features.inhosp_mortality_features: % hadm_ids duplicated',
      dup_n;
  end if;
end $$;


-- outcome counts
select
  y_inhosp_death,
  count(*) as n
from features.split
group by 1
order by 1;


-- stop if outcome has invalid values
do $$
declare
  bad_n bigint;
begin
  select count(*) into bad_n
  from (
    select 1
    from features.split
    where y_inhosp_death is null
       or y_inhosp_death not in (0, 1)
    limit 1
  ) t;

  if bad_n > 0 then
    raise exception 'Found invalid y_inhosp_death values: NULL or not in (0,1)';
  end if;
end $$;


-- train/valid by outcome
select
  split,
  y_inhosp_death,
  count(*) as n
from features.split
group by 1, 2
order by 1, 2;


-- missingness snapshot for V1 model fields
select
  count(*) as n,
  avg((sodium_24h_first     is null)::int)::numeric(10,4) as sodium_null_rate,
  avg((potassium_24h_first  is null)::int)::numeric(10,4) as potassium_null_rate,
  avg((creatinine_24h_first is null)::int)::numeric(10,4) as creatinine_null_rate,
  avg((lactate_24h_first    is null)::int)::numeric(10,4) as lactate_null_rate,
  avg((charlson_min         is null)::int)::numeric(10,4) as charlson_null_rate
from features.split;


-- Charlson component flags are checked in their source view
select
  count(*) as n,
  avg((CHF   is null)::int)::numeric(10,4) as chf_null_rate,
  avg((RENAL is null)::int)::numeric(10,4) as renal_null_rate,
  avg((DM    is null)::int)::numeric(10,4) as dm_null_rate
from features.charlson_flags;


-- confirm split rule lines up with anchor_year
select
  s.split,
  min(p.anchor_year) as min_anchor_year,
  max(p.anchor_year) as max_anchor_year,
  count(*) as n
from features.split s
join mimiciv_hosp.patients p
  on p.subject_id = s.subject_id
group by 1
order by 1;


-- quick sample rows
select
  hadm_id,
  subject_id,
  y_inhosp_death,
  split,
  sodium_24h_first,
  potassium_24h_first,
  creatinine_24h_first,
  lactate_24h_first,
  charlson_min
from features.split
limit 10;