from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re
from urllib.parse import urljoin, urlparse, parse_qs
import requests

logger = logging.getLogger(__name__)

class ReceiptParserError(Exception):
    """Custom exception for errors in the ReceiptParser class."""
    pass

class ReceiptParser:
    def __init__(self, message_body: str):
        self.message_body = message_body

    def parse(self):
        if self.find_taxcom_url(self.message_body) is not None:
            return self.parse_taxcom()
        if self._is_magnit():
            return self.parse_magnit()
        if self._is_pofd():
            return self.parse_pofd()
        if self._is_beeline():
            return self.parse_beeline()
        raise ReceiptParserError("Unknown receipt email template")

    def parse_magnit(self):
        try:
            rows = self._leaf_rows()
            receipt_data = {}

            rnn_idx = self._index_of(rows, r"^ИНН \d+$")
            rnn_cell = self._cell(rows[rnn_idx])
            m = re.search(r"\b(\d{10})\b", rnn_cell)
            rnn = m.group(1) if m else ""
            company = self._cell(rows[rnn_idx - 1])
            address = self._cell(rows[rnn_idx + 1])

            receipt_data["date_purchase"] = datetime.strptime(
                self._find_text(rows, r"^\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}$"), "%d.%m.%Y %H:%M")
            receipt_data["receipt_id"] = self._find_text(rows, r"^N: \d+$").split(":", 1)[1].strip()
            receipt_data["total_sum"] = self._find_pair(rows, r"^ИТОГО:$")[1]

            store_name = re.sub(r"^Магазин\s+", "",
                                self._find_text(rows, r"^Магазин\s+")).strip()
            receipt_data["store"] = {
                "name": store_name,
                "company": company,
                "address": address,
                "rnn": rnn
            }

            items = []
            for i, cells in enumerate(rows):
                if len(cells) != 4 or not self._is_number(cells[1]):
                    continue
                # единица измерения идет следом за признаком предмета расчета
                unit = None
                for next_cells in rows[i + 1:i + 6]:
                    if next_cells[0].startswith("МЕРА КОЛИЧЕСТВА") and len(next_cells) > 1:
                        unit = next_cells[1]
                        break
                items.append({
                    "name": cells[0],
                    "unit": unit,
                    "quantity": cells[1],
                    "price_per_item": cells[2],
                    "amount_price": cells[3]
                })
            receipt_data["items"] = items

        except Exception as e:
            raise ReceiptParserError(
                f"Magnit message body cannot be parsed. Error {e}") from e
        return receipt_data

    def parse_pofd(self):
        try:
            rows = self._leaf_rows()
            receipt_data = {}

            address = self._find_text(rows, r"^\d{6},")
            rnn = self._find_text(rows, r"^ИНН \d+$").split()[1]

            receipt_data["date_purchase"] = datetime.strptime(self._find_pair(rows, r"^Приход$")[1], "%d.%m.%Y %H:%M")
            receipt_data["receipt_id"] = re.search(r"№(\d+)", self._find_text(rows, r"^КАССОВЫЙ ЧЕК №\d+$")).group(1)
            receipt_data["total_sum"] = self._find_pair(rows, r"^ИТОГ$")[1].lstrip("=").strip()

            store_name = self._find_text(rows, r"^Место расчётов:").split(":", 1)[1].strip()
            receipt_data["store"] = {
                "name": store_name,
                "company": None,
                "address": address,
                "rnn": rnn
            }

            items = []
            for i, cells in enumerate(rows):
                if len(cells) != 1:
                    continue
                name_match = re.match(r"^\d+:\s*(.+)$", cells[0])
                if name_match is None:
                    continue
                # следующая строка: "1 шт. x 10.89" (количество, единица, цена за единицу)
                qty_match = None
                for next_cells in rows[i + 1:i + 3]:
                    if len(next_cells) == 1:
                        m = re.match(r"^([\d.,]+)\s+(\S+)\s+x\s+([\d.,]+)$", next_cells[0])
                        if m is not None:
                            qty_match = m
                            break
                if qty_match is None:
                    continue
                qty, unit, price = qty_match.groups()
                # итоговая сумма позиции: строка "Общая стоимость позиции..."
                amount = None
                for next_cells in rows[i + 1:i + 8]:
                    if len(next_cells) == 2 and next_cells[0].startswith("Общая стоимость позиции"):
                        amount = next_cells[1]
                        break
                items.append({
                    "name": name_match.group(1).strip(),
                    "unit": unit,
                    "quantity": qty,
                    "price_per_item": price,
                    "amount_price": amount
                })
            receipt_data["items"] = items

        except Exception as e:
            raise ReceiptParserError(
                f"POFD message body cannot be parsed. Error {e}") from e
        return receipt_data

    def parse_beeline(self):
        try:
            rows = self._leaf_rows()
            receipt_data = {}

            date_pair = self._find_pair(rows, r"^Дата \| Время$")
            date_text, time_text = [p.strip() for p in date_pair[1].split("|")]
            receipt_data["date_purchase"] = datetime.strptime(f"{date_text} {time_text}", "%d.%m.%Y %H:%M")

            receipt_data["receipt_id"] = self._find_pair(rows, r"^Чек №$")[1].strip()
            receipt_data["total_sum"] = self._find_pair(rows, r"^Итог$")[1]

            rnn = self._find_pair(rows, r"^ИНН$")[1]
            store_name = self._find_pair(rows, r"^Место расчетов$")[1]

            company_idx = self._index_of(rows, r"^(ООО|ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ|АО|ЗАО|ПАО|ИП)\s")
            company = self._cell(rows[company_idx])
            address = self._cell(rows[company_idx + 1])

            receipt_data["store"] = {
                "name": store_name,
                "company": company,
                "address": address,
                "rnn": rnn
            }

            items = []
            for i, cells in enumerate(rows):
                if len(cells) != 2 or cells[0] != "Цена * Кол":
                    continue
                # "124.99 * 1 шт. = 124.99"
                expr = re.match(r"^([\d.,]+)\s*\*\s*([\d.,]+)\s*(\S+)\s*=\s*([\d.,]+)$", cells[1])
                if expr is None:
                    continue
                price, qty, unit, amount = expr.groups()
                # название позиции - строка выше, вида ["3 .", "СПз Хлеб..."]
                name = None
                for prev_cells in reversed(rows[max(0, i - 3):i]):
                    if len(prev_cells) == 2 and re.match(r"^\d+\s*\.$", prev_cells[0]):
                        name = prev_cells[1]
                        break
                if name is None:
                    continue
                items.append({
                    "name": name,
                    "unit": unit,
                    "quantity": qty,
                    "price_per_item": price,
                    "amount_price": amount
                })
            receipt_data["items"] = items

        except Exception as e:
            raise ReceiptParserError(
                f"Beeline message body cannot be parsed. Error {e}") from e
        return receipt_data

    @staticmethod
    def _clean(text: str) -> str:
        """Убирает zero-width и неразрывные символы из текста ячейки."""
        text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
        text = re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()
        return text

    def _leaf_rows(self):
        """Возвращает строки таблиц чека без строк-контейнеров с вложенными таблицами.
        Каждый элемент - список текстов ячеек одной строки.
        """
        soup = BeautifulSoup(self.message_body, "html.parser")
        rows = []
        for tr in soup.find_all("tr"):
            cells = tr.find_all(["td", "th"], recursive=False)
            if not cells or any(td.find("table") is not None for td in cells):
                continue  # строка-контейнер с вложенной таблицей
            texts = [self._clean(td.get_text(" ", strip=True)) for td in cells]
            texts = [t for t in texts if t]
            if texts:
                rows.append(texts)
        return rows

    @staticmethod
    def _cell(cells) -> str:
        return cells[0] if cells else ""

    @staticmethod
    def _is_number(value: str) -> bool:
        return bool(re.match(r"^[\d.,]+$", value))

    @staticmethod
    def _index_of(rows, pattern: str) -> int:
        regex = re.compile(pattern)
        for i, cells in enumerate(rows):
            if any(regex.match(c) for c in cells):
                return i
        raise ReceiptParserError(f"Row matching /{pattern}/ not found")

    @classmethod
    def _find_text(cls, rows, pattern: str) -> str:
        """Возвращает текст ячейки, совпавшей с pattern."""
        regex = re.compile(pattern)
        for cells in rows:
            for c in cells:
                if regex.match(c):
                    return c
        raise ReceiptParserError(f"Cell matching /{pattern}/ not found")

    @classmethod
    def _find_pair(cls, rows, label_pattern: str):
        """Находит строку [label, value], где label совпадает с pattern."""
        regex = re.compile(label_pattern)
        for cells in rows:
            if len(cells) == 2 and regex.match(cells[0]):
                return cells
        raise ReceiptParserError(
            f"Row pair with label /{label_pattern}/ not found")

    def _is_magnit(self) -> bool:
        return "ofd-magnit.ru" in self.message_body

    def _is_pofd(self) -> bool:
        return "chek.pofd.ru" in self.message_body

    def _is_beeline(self) -> bool:
        return "ofd.beeline.ru" in self.message_body or "ofdreceipt@beeline.ru" in self.message_body

    def parse_taxcom(self):
        try:
            url = self.find_taxcom_url(self.message_body)
            if url is None:
                raise ReceiptParserError("Receipt URL not found")
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            receipt_data = {}

            receipt_data["receipt_id"] = soup.find("span", class_="receipt-value-1042").text.strip()

            date_purchase = soup.find("span", class_="receipt-value-1012").text
            receipt_data["date_purchase"] = datetime.strptime(date_purchase, "%d.%m.%y %H:%M")

            receipt_data["total_sum"] = soup.find("span", class_="receipt-value-1020").text

            store_name = soup.find("span", class_="receipt-value-1187").text.strip()
            store_company = soup.find("span", class_="receipt-subtitle").text.strip()
            store_address = soup.find("span", class_="receipt-value-1009").text.strip()
            store_rnn = soup.find("span", class_="receipt-value-1018").text.strip()[4:]
            receipt_data["store"] = {
                "name": store_name,
                "company": store_company,
                "address": store_address,
                "rnn": store_rnn
            }

            receipt_data["items"] = []
            for item in soup.find_all('div', class_='item'):
                str = item.find("span", class_="receipt-value-1030").text
                idx_delimiter = str.index(';')
                name = str[:idx_delimiter].strip()
                unit = str[idx_delimiter + 2:idx_delimiter + 4]
                quantity = item.find("span", class_="receipt-value-1023").text
                price_per_item = item.find("span", class_="receipt-value-1079").text
                amount_price = item.find("span", class_="receipt-value-1043").text

                receipt_data["items"].append({
                    "name": name,
                    "unit": unit,
                    "quantity": quantity,
                    "price_per_item": price_per_item,
                    "amount_price": amount_price
                })

        except Exception as e:
            raise ReceiptParserError(f"Message body cannot be parsed. Error {e}") from e
        return receipt_data

    def find_taxcom_url(self, html: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")

        for link in soup.find_all("a", href=True):
            url = urljoin("https://receipt.taxcom.ru/", link["href"])
            parsed = urlparse(url)
            query = parse_qs(parsed.query)

            if (
                parsed.scheme == "https"
                and parsed.hostname == "receipt.taxcom.ru"
                and parsed.path.rstrip("/") == "/v01/show"
                and query.get("id")
            ):
                return url

        return None