{{
    config(
        materialized='table'
    )
}}
with source as (
    select md5(concat(receipt_id, date_purchase))::bytea     as receipt_hash,
           receipt_id                                        as receipt_id,
           date_purchase                                     as date_purchase,
           current_timestamp                                 as load_date,
           '{{ source('raw','receipts') }}'                  as record_source
      from {{ source('raw','receipts') }}
)

select distinct *
  from source
where receipt_hash not in (
    select receipt_hash from {{ this }}
)