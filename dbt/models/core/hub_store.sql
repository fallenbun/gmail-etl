{{
    config(
        materialized='incremental',
        unique_key='store_hash'
    )
}}
with source as (
    select store_hash,
           rnn,
           current_timestamp::timestamp  as load_date,
           '{{ ref('store_dedup') }}'    as record_source
      from {{ ref('store_dedup') }}
)

select *
  from source

{% if is_incremental() %}
 where store_hash not in (select store_hash from {{ this }})
{% endif %}