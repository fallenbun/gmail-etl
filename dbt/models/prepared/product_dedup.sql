with source as (
    select *,
           md5(product_name)::bytea                          as product_hash,
           md5(concat(receipt_id, date_purchase))::bytea     as receipt_hash
      from {{ ref('receipt_items') }}
),
dedup as (
    select raw_id,
           product_hash,
           receipt_hash,
           product_name                    as name,
           unit,
           quantity,
           amount_price,
           price_per_item,
           loaded_at,
           row_number() over(
            partition by product_hash
                order by loaded_at desc)   as rn
      from source
),
combine as (
    select raw_id,
           product_hash,
           sum(quantity)        as quantity,
           sum(amount_price)    as total_price
      from source
  group by raw_id,
           product_hash
    having count(*) > 1
)

select dedup.raw_id,
       dedup.product_hash,
       dedup.receipt_hash,
       dedup.name,
       dedup.unit,
       case when combine.quantity is not null then
            combine.quantity
        else dedup.quantity
       end as quantity,
       case when combine.total_price is not null then
        combine.total_price
        else dedup.amount_price
       end as total_price,
       dedup.price_per_item,
       dedup.loaded_at
  from dedup
left join combine
using (raw_id, product_hash)
where rn = 1