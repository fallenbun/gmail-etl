import os.path
from pathlib import Path
import os.path
from pathlib import Path
from client import GmailApi
import json
from gmail_client import GmailApi
from receipt_parser import ReceiptParser
from file_writer import JsonFileWriter
import logging

logger = logging.getLogger(__name__)

FILE_PATH = os.path.dirname(os.path.realpath(__file__))
RAWDATA_PATH = str(Path(FILE_PATH, "data/raw_data.json"))
PARSED_DATA_PATH = str(Path(FILE_PATH, "data/parsed_data.json"))
PARSED_DATA_CSV_PATH = str(Path(FILE_PATH, "data/parsed_data.csv"))
from bs4 import BeautifulSoup
import postgres.crud as pg

FILE_PATH = os.path.dirname(os.path.realpath(__file__))
RAWDATA_PATH = str(Path(FILE_PATH, "raw_data.json"))
PARSED_DATA_PATH = str(Path(FILE_PATH, "parsed_data.json"))


def main():
    """
    client = GmailApi()
    sender = "ОФД Такском"
    contents = {}
    # получить список id, threadId писем
    emails = client.find_emails(sender)
    # получить id каждого письма
    email_ids = [email["id"] for email in emails]
    # получить тело письма
    for email_id in email_ids:
        contents[email_id] = client.get_email(email_id)

    # сохранить тело письма
    with open(RAWDATA_PATH, 'w') as f:
        json.dump(contents, f)
    """

if __name__ == "__main__":
    main()
