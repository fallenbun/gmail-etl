{{
    config(
        materialized='incremental',
        unique_key='receipt_store_hash'
    )
}}

with source as (
    select *,
           md5(concat(receipt_hash, store_hash))::bytea           as receipt_store_hash
      from (select md5(concat(receipt_id, date_purchase))::bytea  as receipt_hash,
                   md5(rnn)::bytea                                as store_hash,
                   current_timestamp::timestamp                   as load_date,
                   '{{ref('receipt_items')}}'                     as record_source
              from {{ref('receipt_items')}}) as t
),
dedup as (
    select receipt_store_hash,
           receipt_hash,
           store_hash,
           load_date,
           record_source,
           row_number() over(
            partition by receipt_store_hash
                order by load_date desc)    as rn
      from source
)

select receipt_store_hash,
       receipt_hash,
       store_hash,
       load_date,
       record_source
  from dedup
 where rn = 1