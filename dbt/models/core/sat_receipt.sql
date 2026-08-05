{{
    config(
        materialized='incremental',
        unique_key=['receipt_hash', 'load_date']
    )
}}

with source as (
    select *,
           current_timestamp::timestamp  as load_date,
           '{{ref('receipt_dedup')}}'    as record_source,
           md5(total::text)::bytea       as hash_diff
      from {{ ref('receipt_dedup') }}
)

select receipt_hash,
       load_date,
       record_source,
       hash_diff,
       total
  from source

{% if is_incremental() %}
where not exists(
    select 1 from {{ this }} st
     where source.receipt_hash = st.receipt_hash
       and st.hash_diff = source.hash_diff
       and source.loaded_at <= st.load_date
    )
{% endif %}