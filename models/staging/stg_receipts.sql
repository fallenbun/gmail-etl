CREATE SCHEMA IF NOT EXISTS stg_raw;

CREATE TABLE stg_raw.stg_receipts (
    raw_id          SERIAL PRIMARY KEY,
    message_id      VARCHAR(16) UNIQUE NOT NULL,
    receipt_id      NUMERIC NOT NULL,
    date_purchase   TIMESTAMP NOT NULL,
    total_sum       DECIMAL(8,2) NOT NULL,
    store_json      JSONB NOT NULL,
    items_json      JSONB NOT NULL,
    full_json       JSONB NOT NULL,
    parsed_at       TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_stg_receipts_rec_id_datep ON stg_raw.stg_receipts(receipt_id, date_purchase);