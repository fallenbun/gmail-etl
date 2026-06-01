import psycopg2
import psycopg2.sql as sql
import json
from datetime import datetime
from gmail_client import GmailApi
from receipt_parser import ReceiptParser
import logging

logger = logging.getLogger(__name__)


class EmailLoader:
    def __init__(self, db_conn: psycopg2.extensions.connection):
        self.conn = db_conn
        self.client = GmailApi()

    def load_emails(self, sender: str):
        messages = self.client.find_emails(sender)
        try:
            for msg in messages:
                if not self._email_exists(msg["id"]):
                    record = self.client.get_email(msg["id"])
                    self._insert_email(record)
        except Exception as error:
            logger.error(f"Cannot load emails: {error}")

    def _email_exists(self, message_id: str):
        try:
            select_query = sql.SQL("SELECT 1 FROM stg_raw.stg_emails WHERE message_id = {}").format(
                sql.Placeholder())
            cur = self.conn.cursor()
            cur.execute(select_query, (message_id,))
            return cur.fetchone()
        except psycopg2.Error as error:
            logger.error(f"Error executing query: {error}")
        finally:
            cur.close()

    def _insert_email(self, record):
        insert_query = sql.SQL("INSERT INTO stg_raw.stg_emails ({}) VALUES ({})").format(
            sql.SQL(', ').join(map(sql.Identifier, record.keys())),
            sql.SQL(', ').join(sql.Placeholder() * len(record.values()))
        )
        record_to_insert = tuple(record.values())
        try:
            cur = self.conn.cursor()
            cur.execute(insert_query, record_to_insert)
            self.conn.commit()
        except psycopg2.Error as error:
            self.conn.rollback()
            logger.error(f"Error executing query: {error}")
        finally:
            cur.close()


class ReceiptLoader:

    def __init__(self, db_conn: psycopg2.extensions.connection):
        self.conn = db_conn

    def load_receipts(self):
        try:
            emails = self._fetch_unparsed()
            for raw_id, msg_id, payload in emails:
                parser = ReceiptParser(payload)
                parsed = parser.parse_lenta()
                record = {
                    "message_id": msg_id,
                    "receipt_id": parsed['receipt_id'],
                    "date_purchase": parsed['date_purchase'],
                    "total_sum": float(parsed['total_sum']),
                    "store_json": json.dumps(parsed['store'], ensure_ascii=False),
                    "items_json": json.dumps(parsed['items'], ensure_ascii=False)
                }
                self._insert_parsed(record)
                self._update_parsed_status(raw_id=raw_id, status=1)
                self.conn.commit()
        except psycopg2.Error as error:
            self.conn.rollback()
            logger.error(f"Fail loading receipts: {error}")

    def _fetch_unparsed(self):
        try:
            query = sql.SQL(
                "SELECT raw_id, message_id, payload_data FROM stg_raw.stg_emails WHERE parse_status = 0")
            cur = self.conn.cursor()
            cur.execute(query)
            return cur.fetchall()
        except psycopg2.Error as error:
            logger.warning(f"Cannot fetch emails: {error}")
        finally:
            cur.close()

    def _insert_parsed(self, dictionary):
        query = sql.SQL("INSERT INTO stg_raw.stg_receipts ({}) VALUES ({})").format(
            sql.SQL(', ').join(map(sql.Identifier, dictionary.keys())),
            sql.SQL(', ').join(sql.Placeholder() * len(dictionary.values()))
        )
        record_to_insert = tuple(dictionary.values())
        try:
            cur = self.conn.cursor()
            cur.execute(query, record_to_insert)
        except psycopg2.Error as error:
            self.conn.rollback()
            logger.error(f"Cannot insert data: {error}")
        finally:
            cur.close()

    def _update_parsed_status(self, raw_id, status):
        query = sql.SQL("UPDATE stg_raw.stg_emails SET parse_status = {}, parsed_at = {} WHERE raw_id = {}").format(
            sql.Placeholder(),
            sql.Placeholder(),
            sql.Placeholder()
        )
        try:
            cur = self.conn.cursor()
            cur.execute(query, (status, datetime.now(), raw_id))
        except psycopg2.Error as error:
            self.conn.rollback()
            logger.error(f"Cannot update status: {error}")
        finally:
            cur.close()
