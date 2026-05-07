# Авторизация, чтение писем по фильтру
import base64
from googleapiclient.errors import HttpError
from datetime import datetime, timezone
from auth.auth import authenticate
import logging

logger = logging.getLogger(__name__)

class GmailApi:
    def __init__(self):
        self.service = authenticate()

    def find_emails(self, sender: str):
        request = (
            self.service.users()
            .messages()
            .list(userId="me", q=f"from:{sender} is:unread", maxResults=200)
        )

        result = self._execute_request(request)
        try:
            messages = result.get('messages', [])
            logger.info(
                f"Retrieved messages matching the '{sender}' query: {messages}")
        except KeyError:
            logger.error(f"No messages found for the sender '{sender}'")
            messages = []

        return messages

    def get_email(self, email_id: str):
        request = (
            self.service.users()
            .messages()
            .get(userId="me", id=email_id)
        )
        result = self._execute_request(request)
        try:
            headers = {h["name"]: h["value"]
                       for h in result.get("payload", {}).get("headers", [])}
            sender = headers.get("From", "")
            if sender:
                sender_email = sender.split("<")[1].rstrip(">").strip()
            received_at = headers.get("Date", "")
            if received_at:
                try:
                    date_dt = datetime.strptime(
                        received_at, "%a, %d %b %Y %H:%M:%S %z")
                    received_at = date_dt.isoformat()
                except Exception as e:
                    logger.error(f"Date 'received_at' cannot be parsed: {received_at}. Error: {e}")

            payload_data = result.get("payload", {}).get("body", {}).get("data", {})
            payload_data = payload_data.replace("-", "+").replace("_", "/")
            decoded = base64.b64decode(payload_data).decode("utf-8")
            try:
                loaded_at = datetime.now(timezone.utc).isoformat(timespec='seconds')
            except Exception as e:
                logger.error(f"Date 'loaded_at' cannot be parsed. Error: {e}")
        except Exception as e:
            logger.error(f"An error of loading email payload_data'{e}")

        return {"message_id": email_id,
                "sender_email": sender_email,
                "received_at": received_at,
                "loaded_at": loaded_at,
                "payload_data": decoded}

    @staticmethod
    def _execute_request(request):
        try:
            return request.execute()
        except HttpError as e:
            logger.critical(f"An error occurred: {e}")
            raise RuntimeError(e)
