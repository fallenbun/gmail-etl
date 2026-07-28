with source as (
    select md5(concat(receipt_id, date_purchase))::bytea     as receipt_hash,
           receipt_id,
           date_purchase,
           total,
           loaded_at
      from {{ ref('receipt_items') }}
),
dedup as (
    select receipt_hash,
           receipt_id,
           date_purchase,
           total,
           loaded_at,
           row_number() over(
            partition by receipt_hash
                order by loaded_at desc)   as rn
      from source
)

select receipt_hash,
       receipt_id,
       date_purchase,
       total,
       loaded_at
  from dedup
 where rn = 1