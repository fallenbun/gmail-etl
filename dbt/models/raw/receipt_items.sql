with source as (
    select raw_id,
           message_id,
           receipt_id,
           date_purchase,
           total_sum,
           loaded_at,
           store_json,
           jsonb_array_elements(items_json)    as element
      from {{ source('raw','receipts') }}
),
items as (
    select raw_id,
           message_id,
           receipt_id,
           date_purchase,
           total_sum                                       as total,
           store_json->>'rnn'                              as rnn,
           store_json->>'name'                             as store_name,
           store_json->>'address'                          as address,
           store_json->>'company'                          as company,
           element ->> 'name'                              as product_name,
           element ->> 'unit'                              as unit,
           (element ->> 'quantity')::numeric(10, 3)        as quantity,
           (element ->> 'amount_price')::numeric(12, 2)    as amount_price,
           (element ->> 'price_per_item')::numeric(12, 2)  as price_per_item,
           loaded_at
      from source
)
select *
  from items