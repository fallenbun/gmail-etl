create table shop(
    shop_id serial primary key,
    company varchar(50) not null,
    name varchar(40) not null,
    rnn varchar(12) not null,
    address text not null,
    date_update date not null
);

create table product (
    product_id serial primary key,
    name varchar(100) not null,
    unit varchar(5) not null ,
    price numeric not null ,
    brand varchar(50),
    date_update date not null
);

create table receipt (
    receipt_id integer,
    date_purchase date ,
    shop_id integer not null,
    total_sum numeric not null,
    date_update date not null,
    primary key (receipt_id, date_purchase),
    foreign key (shop_id) references shop(shop_id) on delete set null
);

create table purchase (
    receipt_id integer,
    date_purchase date,
    product_id integer,
    quantity real not null,
    price_per_unit numeric not null,
    price_promo numeric,
    date_insert date not null,
    foreign key (product_id) references product(product_id) on delete set null,
    foreign key (receipt_id,date_purchase) references receipt(receipt_id, date_purchase) on delete cascade
);