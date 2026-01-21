import base64
from googleapiclient.errors import HttpError

from auth.auth import authenticate


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
            print(
                f"Retrieved messages matching the '{sender}' query: {messages}")
        except KeyError:
            print(f"No messages found for the sender '{sender}'")
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
            data = {}
            data["mime_type"] = result["payload"]["mimeType"]

            headers = result["payload"]["headers"]
            data["subject"] = data["sender"] = data["date"] = ''
            data["contentType"] = ''
            for h in headers:
                name, value = h['name'], h['value']
                if name == 'Subject':
                    data["subject"] = value
                elif name == 'From':
                    data["sender"] = value
                elif name == 'Date':
                    data["date"] = value
                elif name == 'Content-Transfer-Encoding':
                    data["contentType"] = value
            content = result["payload"]["body"]["data"]
            content = content.replace("-", "+").replace("_", "/")
            data["content"] = base64.b64decode(content).decode("utf-8")
        except Exception as e:
            print(e)
        return data

    @staticmethod
    def _execute_request(request):
        try:
            return request.execute()
        except HttpError as e:
            print(f"An error occurred: {e}")
            raise RuntimeError(e)
