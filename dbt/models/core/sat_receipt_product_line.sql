{{
    config(
        materialized='incremental',
        unique_key=['receipt_product_hash', 'load_date']
    )
}}

with source as (
    select *,
           md5(concat(receipt_hash, product_hash))::bytea         as receipt_product_hash,
           current_timestamp::timestamp                           as load_date,
           '{{ref('product_dedup')}}'                             as record_source,
           md5(concat(quantity::text,
                      price_per_item::text,
                      total_price::text))::bytea                  as hash_diff
      from {{ ref('product_dedup') }}
)

select receipt_product_hash,
       load_date,
       record_source,
       hash_diff,
       quantity,
       price_per_item,
       total_price
  from source

{% if is_incremental() %}
where not exists(
    select 1 from {{ this }} st
     where source.receipt_product_hash = st.receipt_product_hash
       and st.hash_diff = source.hash_diff
       and source.loaded_at <= st.load_date
    )
{% endif %}