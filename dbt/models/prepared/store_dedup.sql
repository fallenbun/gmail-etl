with source as (
    select md5(rnn)::bytea    as store_hash,
           rnn,
           store_name         as name,
           address,
           company,
           loaded_at           
      from {{ ref('receipt_items') }}
),
dedup as (
    select store_hash,
           rnn,
           name,
           address,
           company,
           loaded_at,
           row_number() over(
            partition by store_hash 
                order by loaded_at desc)  as rn
      from source
)

select store_hash,
       rnn,
       name,
       address,
       company,
       loaded_at
  from dedup
 where rn = 1