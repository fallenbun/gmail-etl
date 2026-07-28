{{
    config(
        materialized='incremental',
        unique_key='product_hash'
    )
}}
with source as (
    select product_hash,
           name,
           current_timestamp::timestamp  as load_date,
           '{{ ref('product_dedup') }}'  as record_source
    from {{ ref('product_dedup') }}
)
select *
  from source

{% if is_incremental() %}
 where product_hash not in (select product_hash from {{ this }})
{% endif %}