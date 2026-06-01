from config.config import settings
import psycopg2
from loader import EmailLoader, ReceiptLoader
import sys
import logging

logger = logging.getLogger(__name__)


def main():
    FORMAT = "%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
    logging.basicConfig(filename='./py_log.log', encoding="utf-8", level=logging.INFO,
                        filemode='w', format=FORMAT)
    credentials = {
        "host": settings.DB_HOST,
        "port": settings.DB_PORT,
        "user": settings.DB_USER,
        "password": settings.DB_PASSWORD.get_secret_value(),
        "dbname": settings.DB_NAME
    }
    sender = "ОФД Такском"
    try:
        connection = psycopg2.connect(**credentials)
        logger.info(f"Connection succeeded")

        email_loader = EmailLoader(db_conn=connection)
        email_loader.load_emails(sender=sender)

        receipt_loader = ReceiptLoader(db_conn=connection)
        receipt_loader.load_receipts()
    except psycopg2.Error as error:
        logger.error(f"Error connecting to the database: {error}")
        sys.exit()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
