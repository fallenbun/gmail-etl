from bs4 import BeautifulSoup
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ReceiptParserError(Exception):
    """Custom exception for errors in the ReceiptParser class."""
    pass

class ReceiptParser:
    def __init__(self, message_body: str):
        self.message_body = message_body

    def parse_lenta(self):
        try:
            soup = BeautifulSoup(self.message_body, 'html.parser')
            receipt_data = {}

            receipt_data["receipt_id"] = soup.find("span", class_="receipt-value-1042").text.strip()

            date_purchase = soup.find("span", class_="receipt-value-1012").text
            receipt_data["date_purchase"] = datetime.strptime(date_purchase, "%d.%m.%y %H:%M")

            receipt_data["total_sum"] = soup.find("span", class_="receipt-value-1020").text

            store_name = soup.find("span", class_="receipt-value-1187").text.strip()
            store_company = soup.find("span", class_="receipt-subtitle").text.strip()
            store_address = soup.find("span", class_="receipt-value-1009").text.strip()
            store_rnn = soup.find("span", class_="receipt-value-1018").text.strip()[4:]
            receipt_data["store"] = {"name": store_name,
                                     "company": store_company,
                                     "address": store_address,
                                     "rnn": store_rnn}

            receipt_data["items"] = []
            for item in soup.find_all('div', class_='item'):
                str = item.find("span", class_="receipt-value-1030").text
                idx_delimiter = str.index(';')
                name = str[:idx_delimiter].strip()
                unit = str[idx_delimiter + 2:idx_delimiter + 4]
                quantity = item.find("span", class_="receipt-value-1023").text
                price_per_item = item.find("span", class_="receipt-value-1079").text
                amount_price = item.find("span", class_="receipt-value-1043").text

                receipt_data["items"].append(
                    {"name": name,
                     "unit": unit,
                     "quantity": quantity,
                     "price_per_item": price_per_item,
                     "amount_price": amount_price})

        except Exception as e:
            raise ReceiptParserError(f"Message body cannot be parsed. Error {e}") from e
        return receipt_data