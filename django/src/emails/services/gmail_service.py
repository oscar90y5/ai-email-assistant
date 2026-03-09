import base64
import os
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .mail_service import MailService


class GmailAuthError(Exception):
    pass


TOKEN_PATH = "/run/secrets/token.json"


class GmailService(MailService):

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.modify",
    ]

    def __init__(self):
        token_path = TOKEN_PATH

        if not os.path.exists(token_path):
            raise GmailAuthError(f"Gmail token file not found: {token_path}")

        try:
            creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
        except Exception as exc:
            raise GmailAuthError(f"Failed to load Gmail credentials: {exc}") from exc

        if creds.expired:
            if not creds.refresh_token:
                raise GmailAuthError("Gmail token is expired and has no refresh token")
            try:
                creds.refresh(Request())
            except Exception as exc:
                raise GmailAuthError(f"Failed to refresh Gmail token: {exc}") from exc

        self._service = build("gmail", "v1", credentials=creds)

    def fetch_unread(self) -> list[dict]:
        messages_api = self._service.users().messages()
        response = messages_api.list(
            userId="me", labelIds=["UNREAD"], maxResults=100
        ).execute()

        stubs = response.get("messages", [])
        if not stubs:
            return []

        emails = []
        for stub in stubs:
            msg = messages_api.get(userId="me", id=stub["id"], format="full").execute()
            emails.append(self._parse_message(msg))

        return emails

    def mark_as_read(self, email_id: str) -> None:
        self._service.users().messages().modify(
            userId="me",
            id=email_id,
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()

    def archive(self, email_id: str) -> None:
        self._service.users().messages().modify(
            userId="me",
            id=email_id,
            body={"removeLabelIds": ["INBOX"]},
        ).execute()

    def add_label(self, email_id: str, label: str) -> None:
        label_id = self._get_or_create_label(label)
        self._service.users().messages().modify(
            userId="me",
            id=email_id,
            body={"addLabelIds": [label_id]},
        ).execute()

    def _get_or_create_label(self, name: str) -> str:
        response = self._service.users().labels().list(userId="me").execute()
        for existing in response.get("labels", []):
            if existing["name"] == name:
                return existing["id"]

        created = self._service.users().labels().create(
            userId="me", body={"name": name}
        ).execute()
        return created["id"]

    def _parse_message(self, msg: dict) -> dict:
        headers = {
            h["name"].lower(): h["value"]
            for h in msg.get("payload", {}).get("headers", [])
        }

        date_str = headers.get("date", "")
        try:
            received_at = parsedate_to_datetime(date_str)
        except Exception:
            received_at = datetime.now(tz=timezone.utc)

        body = self._extract_body(msg.get("payload", {}))

        return {
            "id": msg["id"],
            "thread_id": msg.get("threadId", ""),
            "subject": headers.get("subject", ""),
            "sender": headers.get("from", ""),
            "recipient": headers.get("to", ""),
            "body": body,
            "received_at": received_at,
            "label_ids": msg.get("labelIds", []),
        }

    def _extract_body(self, payload: dict) -> str:
        mime_type = payload.get("mimeType", "")

        if mime_type == "text/plain":
            data = payload.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

        for part in payload.get("parts", []):
            result = self._extract_body(part)
            if result:
                return result

        return ""
