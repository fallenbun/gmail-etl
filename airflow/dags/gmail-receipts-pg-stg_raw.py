from datetime import datetime
import psycopg2
from airflow.sdk import DAG, task
from airflow.sdk.bases.hook import BaseHook
from loader import ReceiptLoader
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        connection = BaseHook.get_connection("retail")
        return psycopg2.connect(
            host=connection.host,
            port=connection.port,
            user=connection.login,
            password=connection.password,
            dbname=connection.schema,
        )
    except Exception as error:
        raise RuntimeError(f"Error connecting to the database: {error}")


@task()
def load_receipts():
    connection = None
    try:
        connection = get_db_connection()
        if connection is None:
            raise RuntimeError("Database connection was not established")
        receipt_loader = ReceiptLoader(db_conn=connection)
        receipt_loader.load_receipts()
    except Exception as error:
        raise RuntimeError("Error loading receipts") from error
    finally:
        if connection is not None:
            connection.close()

with DAG(
    dag_id="gmail-receipts-pg-stg_raw",
    start_date=datetime(2026, 9, 17),
    schedule="@daily",
    catchup=False,
    tags=["gmail", "receipts"],
) as dag:
    load_receipts()