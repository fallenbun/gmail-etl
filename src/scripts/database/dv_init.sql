CREATE SCHEMA IF NOT EXISTS stg_transformed;

CREATE TABLE stg_transformed.hub_store (
    store_hash    BYTEA         PRIMARY KEY,
    store_rnn     TEXT,
    load_date     TIMESTAMP     NOT NULL  DEFAULT NOW(),
    record_source TEXT          NOT NULL
);
CREATE TABLE stg_transformed.sat_store (
    store_hash    BYTEA         NOT NULL,
    load_date     TIMESTAMP     NOT NULL  DEFAULT NOW(),
    record_source TEXT          NOT NULL,
    hash_diff     BYTEA         NOT NULL,
    store_name    TEXT,
    company       TEXT,
    rnn           VARCHAR(12),
    address       TEXT,
    PRIMARY KEY (store_hash, load_date),
    CONSTRAINT fk_sat_store_hub_store 
        FOREIGN KEY (store_hash) 
        REFERENCES stg_transformed.hub_store(store_hash)
);

CREATE TABLE stg_transformed.hub_receipt (
    receipt_hash  BYTEA         PRIMARY KEY,
    receipt_id    INTEGER       NOT NULL,
    date_purchase TIMESTAMP     NOT NULL,
    load_date     TIMESTAMP     NOT NULL  DEFAULT NOW(),
    record_source TEXT          NOT NULL
);

CREATE TABLE stg_transformed.sat_receipt (
    receipt_hash  BYTEA         NOT NULL,
    load_date     TIMESTAMP     NOT NULL  DEFAULT NOW(),
    record_source TEXT          NOT NULL,
    hash_diff     BYTEA         NOT NULL,
    total         DECIMAL(12,2),
    PRIMARY KEY (receipt_hash, load_date),
    CONSTRAINT fk_sat_receipt_hub_receipt 
        FOREIGN KEY (receipt_hash) 
        REFERENCES stg_transformed.hub_receipt(receipt_hash)
);

CREATE TABLE stg_transformed.hub_product (
    product_hash  BYTEA         PRIMARY KEY,
    product_name  TEXT          NOT NULL,
    load_date     TIMESTAMP     NOT NULL  DEFAULT NOW(),
    record_source TEXT          NOT NULL
);

CREATE TABLE stg_transformed.sat_product (
    product_hash  BYTEA         NOT NULL,
    load_date     TIMESTAMP     NOT NULL  DEFAULT NOW(),
    record_source TEXT          NOT NULL,
    unit          BYTEA,
    hash_diff     BYTEA         NOT NULL,
    PRIMARY KEY (product_hash, load_date),
    CONSTRAINT fk_sat_product_hub_product 
        FOREIGN KEY (product_hash) 
        REFERENCES stg_transformed.hub_product(product_hash)
);

CREATE TABLE stg_transformed.link_receipt_store (
    receipt_store_hash BYTEA     PRIMARY KEY,
    receipt_hash       BYTEA     NOT NULL,
    store_hash         BYTEA     NOT NULL,
    load_date          TIMESTAMP NOT NULL  DEFAULT NOW(),
    record_source      TEXT      NOT NULL,
    CONSTRAINT fk_link_receipt_store_hub_receipt 
        FOREIGN KEY (receipt_hash) 
        REFERENCES stg_transformed.hub_receipt(receipt_hash),
    CONSTRAINT fk_link_receipt_store_hub_store 
        FOREIGN KEY (store_hash) 
        REFERENCES stg_transformed.hub_store(store_hash)
);

CREATE TABLE stg_transformed.link_receipt_product (
    receipt_product_hash BYTEA     PRIMARY KEY,
    receipt_hash         BYTEA     NOT NULL,
    product_hash         BYTEA     NOT NULL,
    product_name         TEXT,
    load_date            TIMESTAMP NOT NULL  DEFAULT NOW(),
    record_source        TEXT      NOT NULL,
    CONSTRAINT fk_link_receipt_product_hub_receipt 
        FOREIGN KEY (receipt_hash) 
        REFERENCES stg_transformed.hub_receipt(receipt_hash),
    CONSTRAINT fk_link_receipt_product_hub_product 
        FOREIGN KEY (product_hash) 
        REFERENCES stg_transformed.hub_product(product_hash)
);

CREATE TABLE stg_transformed.sat_receipt_product_line (
    receipt_product_hash BYTEA         NOT NULL,
    load_date            TIMESTAMP     NOT NULL  DEFAULT NOW(),
    record_source        TEXT          NOT NULL,
    hash_diff            BYTEA         NOT NULL,
    quantity             DECIMAL(10,3),
    price_per_unit       DECIMAL(12,2),
    total_price          DECIMAL(12,2),
    PRIMARY KEY (receipt_product_hash, load_date),
    CONSTRAINT fk_sat_receipt_product_line_link_receipt_product 
        FOREIGN KEY (receipt_product_hash) 
        REFERENCES stg_transformed.link_receipt_product(receipt_product_hash)
);