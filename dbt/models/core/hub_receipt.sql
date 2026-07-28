{{
    config(
        materialized='incremental',
        unique_key='receipt_hash'
    )
}}
with source as (
    select receipt_hash,
           receipt_id,
           date_purchase,
           current_timestamp::timestamp    as load_date,
           '{{ ref('receipt_dedup') }}'    as record_source
      from {{ ref('receipt_dedup') }}
)

select *
  from source

{% if is_incremental() %}
 where receipt_hash not in (select receipt_hash from {{ this }})
{% endif %}