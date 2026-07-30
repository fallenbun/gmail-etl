{{
    config(
        materialized='incremental',
        unique_key='receipt_product_hash'
    )
}}

with source as (
    select *,
           md5(concat(receipt_hash, product_hash))::bytea         as receipt_product_hash
      from (select md5(concat(receipt_id, date_purchase))::bytea  as receipt_hash,
                   md5(product_name)::bytea                       as product_hash,
                   current_timestamp::timestamp                   as load_date,
                   '{{ref('receipt_items')}}'                     as record_source
              from {{ref('receipt_items')}}) as t
),
dedup as (
    select receipt_product_hash,
           receipt_hash,
           product_hash,
           load_date,
           record_source,
           row_number() over(
            partition by receipt_product_hash
                order by load_date desc)                     as rn
      from source)

select receipt_product_hash,
       receipt_hash,
       product_hash,
       load_date,
       record_source
  from dedup
 where rn = 1

{% if is_incremental() %}
   and receipt_product_hash not in (
    select receipt_product_hash from {{ this }})
{% endif %}