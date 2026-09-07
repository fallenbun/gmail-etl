import os
import psycopg2
from loader import EmailLoader
import logging

logger = logging.getLogger(__name__)

def main():
    FORMAT = "[%(asctime)s] p%(process)s - %(levelname)s - %(pathname)s - {%(funcName)s:%(lineno)d}  %(message)s"

    logging.basicConfig(filename='./py_log.log', encoding="utf-8", level=logging.INFO,
                        filemode='w', format=FORMAT, datefmt='%m-%d %H:%M:%S')
    
    credentials = {}
    for key, value in os.environ.items():
       if key.startswith("PY_"):
           credentials[key[3:].lower()] = value

    sender = "ОФД Такском"
    try:
        connection = psycopg2.connect(**credentials)
        logger.info(f"Connection succeeded")
        email_loader = EmailLoader(db_conn=connection)
        email_loader.load_emails(sender=sender)

    except psycopg2.Error as error:
        logger.error(f"Error connecting to the database: {error}")
    finally:
        connection.close()

if __name__ == "__main__":
    main()
