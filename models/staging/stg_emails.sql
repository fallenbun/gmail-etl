CREATE SCHEMA IF NOT EXISTS stg_raw;

CREATE TABLE stg_raw.stg_emails (
    raw_id          SERIAL PRIMARY KEY,
    message_id      VARCHAR(16) UNIQUE NOT NULL,
    sender_email    TEXT NOT NULL,
    received_at     TIMESTAMP NOT NULL,
    loaded_at       TIMESTAMP NOT NULL,
    payload_data    TEXT NOT NULL,
    parse_status    NUMERIC(1) DEFAULT 0, -- 0 - new / 1 - parsed / 2 - error
    parsed_at       TIMESTAMP
);

CREATE INDEX idx_stg_emails_msg_id ON stg_raw.stg_emails(message_id)