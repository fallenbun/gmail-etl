{{
    config(
        materialized='view'
    )
}}

with source as (
    select item.raw_id,
           item.element ->> 'name'                              as product_name,
           item.element ->> 'unit'                              as unit,
           (item.element ->> 'quantity')::numeric(10, 3)        as quantity,
           (item.element ->> 'amount_price')::numeric(12, 2)    as amount_price,
           (item.element ->> 'price_per_item')::numeric(12, 2)  as price_per_item
      from (select raw_id,
                   jsonb_array_elements(items_json) as element
              from {{ source('raw','receipts') }}) as item
)
select md5(product_name)::bytea as product_hash,
       raw_id,
       product_name,
       unit,
       sum(quantity)            as quantity,
       sum(amount_price)        as total_price,
       price_per_item
  from source
 group by raw_id,
          product_name,
          unit,
          price_per_item