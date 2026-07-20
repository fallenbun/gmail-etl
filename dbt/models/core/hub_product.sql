{{
    config(
        materialized='table'
    )
}}
with source as (
    select product_hash,
           product_name,
           current_timestamp                as load_date,
           '{{ ref('receipt_items') }}'     as record_source
    from {{ ref('receipt_items') }}
)

select distinct *
  from source
where product_hash not in (
    select product_hash from {{ this }}
)