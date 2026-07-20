{{
    config(
        materialized='table'
    )
}}
with source as (
    select md5(store_json->>'rnn')::bytea     as store_hash,
           store_json->>'rnn'                 as store_rnn,
           current_timestamp                  as load_date,
           '{{ source('raw','receipts') }}'   as record_source
      from {{ source('raw','receipts') }}
)

select distinct *
  from source
where store_hash not in (
    select store_hash from {{ this }}
)