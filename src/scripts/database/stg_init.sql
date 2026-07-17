CREATE SCHEMA IF NOT EXISTS stg_raw;

CREATE TABLE IF NOT EXISTS stg_raw.stg_emails (
    raw_id          SERIAL PRIMARY KEY,
    message_id      VARCHAR(16) UNIQUE NOT NULL,
    sender_email    TEXT NOT NULL,
    received_at     TIMESTAMP NOT NULL,
    payload_data    TEXT NOT NULL,
    loaded_at       TIMESTAMP DEFAULT now(),
    parse_status    NUMERIC(1) DEFAULT 0, -- 0 - new / 1 - parsed / 2 - error
    parsed_at       TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stg_raw.stg_receipts (
    raw_id          SERIAL PRIMARY KEY,
    message_id      VARCHAR(16) UNIQUE NOT NULL,
    receipt_id      VARCHAR(8) NOT NULL,
    date_purchase   TIMESTAMP NOT NULL,
    total_sum       DECIMAL(8,2) NOT NULL,
    store_json      JSONB NOT NULL,
    items_json      JSONB NOT NULL,
    loaded_at       TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_stg_emails_msg_id ON stg_raw.stg_emails(message_id);
CREATE INDEX idx_stg_receipts_rec_id_dt ON stg_raw.stg_receipts(receipt_id, date_purchase);