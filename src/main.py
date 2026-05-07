from pathlib import Path
from gmail_client import GmailApi
from file_writer import JsonFileWriter
from receipt_parser import ReceiptParser
import logging

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(filename='./py_log.log', encoding="utf-8", level=logging.INFO,
                        filemode='w', format="%(asctime)s - %(levelname)s - %(message)s")
    BASE_DIR = Path(__file__).parent.parent
    RAWDATA_PATH = BASE_DIR.joinpath('raw_data', 'staging')

    client = GmailApi()
    writer = JsonFileWriter(base_dir=RAWDATA_PATH)
    
    sender = "ОФД Такском"
    messages = client.find_emails(sender)
    for msg in messages:
        if not writer.exists(msg["id"]):
            full_msg = client.get_email(msg["id"])
            parser = ReceiptParser(message_body=full_msg["payload_data"])
            full_msg["parsed"] = parser.parse_lenta()
            writer.save(full_msg)
        


if __name__ == "__main__":
    main()
