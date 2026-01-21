from client import GmailApi
import json
from bs4 import BeautifulSoup


def main():
    """
    client = GmailApi()
    # sender = "check@e-check.sportmaster.ru"
    sender = "ОФД Такском"
    contents = {}
    # получить список id, threadId писем
    emails = client.find_emails(sender)
    # получить id каждого письма
    email_ids = [email["id"] for email in emails]
    # получить тело письма
    for email_id in email_ids:
        contents[email_id] = client.get_email(email_id)

    with open('raw_data.json', 'w') as f:
        json.dump(contents, f)
    """
    save_to_file(parse_data())


def parse_data():
    with open('raw_data.json', 'r') as f:
        d = json.load(f)
    for key in d.keys():
        soup = BeautifulSoup(d[key]["content"], 'html.parser')
        receipt_data = {}
        receipt_data["shop_name"] = soup.find(
            "span", class_="receipt-value-1187").text.strip()
        receipt_data["shop_company"] = soup.find(
            "span", class_="receipt-subtitle").text.strip()
        receipt_data["shop_address"] = soup.find(
            "span", class_="receipt-value-1009").text.strip()
        receipt_data["shop_rnn"] = soup.find(
            "span", class_="receipt-value-1018").text.strip()[4:]
        receipt_data["date_purchase"] = soup.find(
            "span", class_="receipt-value-1012").text
        receipt_data["receipt_id"] = soup.find(
            "span", class_="receipt-value-1042").text.strip()
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
        receipt_data["total_sum"] = soup.find(
            "span", class_="receipt-value-1020").text
        return receipt_data


def save_to_file(parsed_data):
    with open('parsed_data.json', 'w') as f:
        json.dump(parsed_data, f, indent=4)


if __name__ == "__main__":
    main()
