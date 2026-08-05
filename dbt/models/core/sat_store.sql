{{
    config(
        materialized='incremental',
        unique_key=['store_hash', 'load_date']
    )
}}

with source as (
    select *,
           current_timestamp::timestamp                      as load_date,
           '{{ref('store_dedup')}}'                          as record_source,
           md5(concat(rnn, name, company, address))::bytea   as hash_diff
      from {{ ref('store_dedup') }}
)

select store_hash,
       load_date,
       record_source,
       hash_diff,
       rnn,
       name,
       company,
       address
  from source

{% if is_incremental() %}
where not exists(
    select 1 from {{ this }} st
     where source.store_hash = st.store_hash
       and st.hash_diff = source.hash_diff
       and source.loaded_at <= st.load_date
    )
{% endif %}