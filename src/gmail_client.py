# Авторизация, чтение писем по фильтру
import base64
from googleapiclient.errors import HttpError
from datetime import datetime
from email.utils import parsedate_to_datetime
from auth.auth import authenticate
import logging

logger = logging.getLogger(__name__)

class GmailApi:
    def __init__(self):
        self.service = authenticate()

    def find_emails(self, senders: list[str]):
        query = self._build_query(senders)
        messages = []
        page_token = None
        while True:
            request = (
                self.service.users()
                .messages()
                .list(userId="me", q=query, maxResults=200, pageToken=page_token)
            )
            result = self._execute_request(request)
            messages = result.get("messages", [])
            page_token = result.get("nextPageToken")
            if not page_token:
                break
        return messages

    def get_email(self, email_id: str):
        request = (
            self.service.users()
            .messages()
            .get(userId="me", id=email_id, format="full")
        )
        result = self._execute_request(request)
        payload = result.get("payload", {})
        try:
            headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
            sender_email = self._parse_sender(headers.get("From", ""))
            received_at = self._parse_date(headers.get("Date", ""))
            decoded = self._extract_body(payload, email_id)
        except Exception as e:
            logger.error(f"An error of loading email {email_id}: {e}")
            raise

        return {"message_id": email_id,
                "sender_email": sender_email,
                "received_at": received_at,
                "payload_data": decoded}

    def _build_query(self, senders: list[str]) -> str:
        senders_query = " ".join(f"from:{sender}" for sender in senders)
        return f"{{{senders_query}}} is:unread"
    
    @staticmethod
    def _parse_sender(sender: str) -> str:
        if "<" in sender and ">" in sender:
            return sender.split("<", 1)[1].split(">", 1)[0].strip()
        return sender.strip()

    @staticmethod
    def _parse_date(received_at: str):
        if not received_at:
            return None
        try:
            return datetime.strptime(received_at, "%a, %d %b %Y %H:%M:%S %z")
        except Exception:
            # запасной разбор для нестандартных дат (email.utils понимает почти все RFC 2822)
            try:
                return parsedate_to_datetime(received_at)
            except Exception as e:
                logger.error(f"Date 'received_at' cannot be parsed: {received_at}. Error: {e}")
                return None

    def _extract_body(self, payload: dict, email_id: str) -> str:
        """Возвращает текст тела письма (HTML предпочтительно) из payload Gmail.
        У простых писем данные в payload.body.data, у multipart - в рекурсивно
        вложенных parts[].body.data.
        """
        part = self._find_body_part(payload)
        if part is None:
            raise ValueError(f"Body part not found in payload of message {email_id}")

        data = part.get("body").get("data")
        padded = data + "=" * (-len(data) % 4)
        raw = base64.urlsafe_b64decode(padded)
        return raw.decode("utf-8")

    @classmethod
    def _find_body_part(cls, payload: dict) -> dict | None:
        body = payload.get("body") or {}
        if payload.get("mimeType") in ("text/html", "text/plain") and body.get("data"):
            return payload

        part = None
        for part in payload.get("parts") or []:
            found = cls._find_body_part(part)
            if found is None:
                continue
            if found.get("mimeType") in ("text/html", "text/plain"):
               return found

    @staticmethod
    def _execute_request(request):
        try:
            return request.execute()
        except HttpError as e:
            logger.critical(f"An error occurred: {e}")
            raise RuntimeError(e)
