import os.path
from pathlib import Path
import json
from bs4 import BeautifulSoup

class ReceiptParser:
    def __init__(self, full_msg):
        self.full_msg = full_msg
    
    def parse_lenta(self):
    
        FILE_PATH = os.path.dirname(os.path.realpath(__file__))
        RAWDATA_PATH = Path(FILE_PATH, "data/raw_data.json")

        with open(RAWDATA_PATH, 'r') as f:
            d = json.load(f)

        for key in d.keys():
            soup = BeautifulSoup(d[key]["content"], 'html.parser')
            receipt_data = {}

            receipt_data["receipt_id"] = soup.find(
                "span", class_="receipt-value-1042").text.strip()
            receipt_data["date_purchase"] = soup.find(
                "span", class_="receipt-value-1012").text
            receipt_data["total_sum"] = soup.find(
                "span", class_="receipt-value-1020").text

            store_name = soup.find(
                "span", class_="receipt-value-1187").text.strip()
            store_company = soup.find(
                "span", class_="receipt-subtitle").text.strip()
            store_address = soup.find(
                "span", class_="receipt-value-1009").text.strip()
            store_rnn = soup.find(
                "span", class_="receipt-value-1018").text.strip()[4:]
            receipt_data["store"] = {"name": store_name, "company": store_company,
                                        "address": store_address, "rnn": store_rnn}

            receipt_data["products"] = []
            for item in soup.find_all('div', class_='item'):
                str = item.find("span", class_="receipt-value-1030").text
                idx_delimiter = str.index(';')
                name = str[:idx_delimiter].strip()
                unit = str[idx_delimiter + 2:idx_delimiter + 4]
                quantity = item.find("span", class_="receipt-value-1023").text
                price_per_unit = item.find(
                    "span", class_="receipt-value-1079").text
                amount_price = item.find("span", class_="receipt-value-1043").text
                if float(price_per_unit) == 0:
                    continue

                receipt_data["products"].append(
                    {"name": name, "unit": unit, "quantity": quantity, "price_per_unit": price_per_unit, "amount_price": amount_price})

            return receipt_data