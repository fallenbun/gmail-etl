import psycopg2
import psycopg2.sql as sql
import json
import traceback
from datetime import datetime, timezone
from gmail_client import GmailApi
from receipt_parser import ReceiptParser, ReceiptParserError
import logging

logger = logging.getLogger(__name__)


class EmailLoader:
    def __init__(self, db_conn: psycopg2.extensions.connection):
        self.conn = db_conn
        self.client = GmailApi()

    def load_emails(self, senders: list[str]):
        messages = self.client.find_emails(senders)
        for msg in messages:
            try:
                if not self._email_exists(msg["id"]):
                    record = self.client.get_email(msg["id"])
                    self._insert_email(record)
            except Exception as error:
                logger.error(f"Cannot load email {msg["id"]}: {error}")

    def _email_exists(self, message_id: str):
        cur = None
        try:
            select_query = sql.SQL("SELECT 1 FROM stg_raw.emails WHERE message_id = {}").format(
                sql.Placeholder())
            cur = self.conn.cursor()
            cur.execute(select_query, (message_id,))
            return cur.fetchone()
        except psycopg2.Error as error:
            logger.error(f"Error executing query: {error}")
        finally:
            if cur is not None:
                cur.close()

    def _insert_email(self, record):
        insert_query = sql.SQL("INSERT INTO stg_raw.emails ({}) VALUES ({})").format(
            sql.SQL(', ').join(map(sql.Identifier, record.keys())),
            sql.SQL(', ').join(sql.Placeholder() * len(record.values()))
        )
        record_to_insert = tuple(record.values())
        cur = None
        try:
            cur = self.conn.cursor()
            cur.execute(insert_query, record_to_insert)
            self.conn.commit()
        except psycopg2.Error as error:
            self.conn.rollback()
            logger.error(f"Error executing query: {error}")
        finally:
            if cur is not None:
                cur.close()


class ReceiptLoader:

    def __init__(self, db_conn: psycopg2.extensions.connection):
        self.conn = db_conn

    def load_receipts(self):
        emails = self._fetch_unparsed()
        for raw_id, msg_id, payload in emails:
            try:
                parser = ReceiptParser(payload)
                parsed = parser.parse_taxcom()
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
                logger.error("Fail loading receipt %s: %s", msg_id, error)
                self._update_parsed_status(
                    raw_id=raw_id,
                    status=-1,
                    msg_id=msg_id,
                    error_traceback=traceback.format_exc(),
                )
                self.conn.commit()
                raise RuntimeError(f"Fail loading receipt {msg_id}: {error}") from error
            except ReceiptParserError as error:
                logger.error("Fail loading receipt %s: %s", msg_id, error)
                self._update_parsed_status(
                    raw_id=raw_id,
                    status=-1,
                    msg_id=msg_id,
                    error_traceback=traceback.format_exc()
                )
                self.conn.commit()

    def _fetch_unparsed(self):
        cur = None
        try:
            query = sql.SQL(
                "SELECT raw_id, message_id, payload_data FROM stg_raw.emails WHERE parse_status <> 1")
            cur = self.conn.cursor()
            cur.execute(query)
            return cur.fetchall()
        except psycopg2.Error as error:
            raise RuntimeError(f"Cannot fetch emails: {error}") from error
        finally:
            if cur is not None:
                cur.close()

    def _insert_parsed(self, dictionary):
        cur = None
        query = sql.SQL("INSERT INTO stg_raw.receipts ({}) VALUES ({})").format(
            sql.SQL(', ').join(map(sql.Identifier, dictionary.keys())),
            sql.SQL(', ').join(sql.Placeholder() * len(dictionary.values()))
        )
        record_to_insert = tuple(dictionary.values())
        try:
            cur = self.conn.cursor()
            cur.execute(query, record_to_insert)
        finally:
            if cur is not None:
                cur.close()

    def _update_parsed_status(self, raw_id, status, msg_id=None, error_traceback=None):
        cur = None
        query = sql.SQL("UPDATE stg_raw.emails SET parse_status = {}, parsed_at = {} WHERE raw_id = {}").format(
            sql.Placeholder(),
            sql.Placeholder(),
            sql.Placeholder()
        )
        try:
            cur = self.conn.cursor()
            if status == -1:
                query_error = sql.SQL("INSERT INTO stg_raw.email_errors (message_id, traceback) VALUES ({}, {})").format(
                    sql.Placeholder(),
                    sql.Placeholder()
                )
                cur.execute(query_error, (msg_id, error_traceback))
            cur.execute(query, (status, datetime.now(timezone.utc), raw_id))
        except psycopg2.Error as error:
            self.conn.rollback()
            raise RuntimeError(f"Cannot update status {msg_id}: {error}") from error
        finally:
            if cur is not None:
                cur.close()
