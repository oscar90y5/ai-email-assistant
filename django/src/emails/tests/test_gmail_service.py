import base64
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from django.test import TestCase

from emails.services.gmail_service import GmailAuthError, GmailService


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode()


def _make_message(
    msg_id="msg1",
    thread_id="thread1",
    subject="Test Subject",
    sender="sender@example.com",
    recipient="me@example.com",
    date="Mon, 01 Jan 2024 10:00:00 +0000",
    body_text="Hello World",
    label_ids=None,
):
    if label_ids is None:
        label_ids = ["INBOX", "UNREAD"]
    return {
        "id": msg_id,
        "threadId": thread_id,
        "labelIds": label_ids,
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "Subject", "value": subject},
                {"name": "From", "value": sender},
                {"name": "To", "value": recipient},
                {"name": "Date", "value": date},
            ],
            "body": {"data": _b64(body_text)},
            "parts": [],
        },
    }


def _make_service_mock(messages_list_response=None, message_get_response=None, labels=None):
    mock_service = MagicMock()

    messages_api = mock_service.users.return_value.messages.return_value
    labels_api = mock_service.users.return_value.labels.return_value

    # messages.list
    messages_api.list.return_value.execute.return_value = (
        messages_list_response or {"messages": []}
    )
    # messages.get
    messages_api.get.return_value.execute.return_value = (
        message_get_response or _make_message()
    )
    # messages.modify
    messages_api.modify.return_value.execute.return_value = {}

    # labels.list
    labels_api.list.return_value.execute.return_value = {
        "labels": labels or []
    }
    # labels.create
    labels_api.create.return_value.execute.return_value = {"id": "Label_new", "name": "new-label"}

    return mock_service


def _valid_creds_mock(expired=False, has_refresh=True):
    creds = MagicMock()
    creds.expired = expired
    creds.refresh_token = "refresh-token" if has_refresh else None
    return creds


PATCH_BUILD = "emails.services.gmail_service.build"
PATCH_CREDS = "emails.services.gmail_service.Credentials.from_authorized_user_file"
PATCH_REQUEST = "emails.services.gmail_service.Request"
PATCH_TOKEN_PATH = "emails.services.gmail_service.TOKEN_PATH"


class GmailServiceInitTest(TestCase):

    def test_raises_if_token_file_not_found(self):
        with patch(PATCH_TOKEN_PATH, "/nonexistent/token.json"):
            with self.assertRaises(GmailAuthError):
                GmailService()

    def test_raises_if_token_expired_without_refresh_token(self):
        creds = _valid_creds_mock(expired=True, has_refresh=False)
        with patch(PATCH_TOKEN_PATH, "/fake/token.json"):
            with patch("os.path.exists", return_value=True):
                with patch(PATCH_CREDS, return_value=creds):
                    with self.assertRaises(GmailAuthError):
                        GmailService()

    def test_refreshes_token_if_expired_with_refresh_token(self):
        creds = _valid_creds_mock(expired=True, has_refresh=True)
        mock_service = _make_service_mock()
        with patch(PATCH_TOKEN_PATH, "/fake/token.json"):
            with patch("os.path.exists", return_value=True):
                with patch(PATCH_CREDS, return_value=creds):
                    with patch(PATCH_REQUEST) as mock_request:
                        with patch(PATCH_BUILD, return_value=mock_service):
                            GmailService()
                            creds.refresh.assert_called_once_with(mock_request.return_value)


class GmailServiceFetchUnreadTest(TestCase):

    def _build_service(self, mock_service):
        creds = _valid_creds_mock()
        with patch(PATCH_TOKEN_PATH, "/fake/token.json"):
            with patch("os.path.exists", return_value=True):
                with patch(PATCH_CREDS, return_value=creds):
                    with patch(PATCH_BUILD, return_value=mock_service):
                        return GmailService()

    def test_fetch_unread_returns_parsed_emails(self):
        msg = _make_message(msg_id="msg1", subject="Hello", body_text="Body text")
        mock_service = _make_service_mock(
            messages_list_response={"messages": [{"id": "msg1"}]},
            message_get_response=msg,
        )
        svc = self._build_service(mock_service)

        result = svc.fetch_unread()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "msg1")
        self.assertEqual(result[0]["subject"], "Hello")
        self.assertEqual(result[0]["body"], "Body text")
        self.assertEqual(result[0]["sender"], "sender@example.com")

    def test_fetch_unread_returns_empty_list_when_inbox_empty(self):
        mock_service = _make_service_mock(
            messages_list_response={"messages": []},
        )
        svc = self._build_service(mock_service)

        result = svc.fetch_unread()

        self.assertEqual(result, [])

    def test_fetch_unread_returns_empty_list_when_no_messages_key(self):
        mock_service = _make_service_mock(
            messages_list_response={},
        )
        svc = self._build_service(mock_service)

        result = svc.fetch_unread()

        self.assertEqual(result, [])


class GmailServiceModifyTest(TestCase):

    def _build_service(self, mock_service):
        creds = _valid_creds_mock()
        with patch(PATCH_TOKEN_PATH, "/fake/token.json"):
            with patch("os.path.exists", return_value=True):
                with patch(PATCH_CREDS, return_value=creds):
                    with patch(PATCH_BUILD, return_value=mock_service):
                        return GmailService()

    def test_mark_as_read_calls_modify_with_remove_unread(self):
        mock_service = _make_service_mock()
        svc = self._build_service(mock_service)

        svc.mark_as_read("msg1")

        mock_service.users().messages().modify.assert_called_with(
            userId="me",
            id="msg1",
            body={"removeLabelIds": ["UNREAD"]},
        )

    def test_archive_calls_modify_with_remove_inbox(self):
        mock_service = _make_service_mock()
        svc = self._build_service(mock_service)

        svc.archive("msg1")

        mock_service.users().messages().modify.assert_called_with(
            userId="me",
            id="msg1",
            body={"removeLabelIds": ["INBOX"]},
        )

    def test_add_label_uses_existing_label(self):
        mock_service = _make_service_mock(
            labels=[{"id": "Label_123", "name": "important"}]
        )
        svc = self._build_service(mock_service)

        svc.add_label("msg1", "important")

        mock_service.users().labels().create.assert_not_called()
        mock_service.users().messages().modify.assert_called_with(
            userId="me",
            id="msg1",
            body={"addLabelIds": ["Label_123"]},
        )

    def test_add_label_creates_label_if_not_exists(self):
        mock_service = _make_service_mock(labels=[])
        mock_service.users().labels().create.return_value.execute.return_value = {
            "id": "Label_new",
            "name": "new-label",
        }
        svc = self._build_service(mock_service)

        svc.add_label("msg1", "new-label")

        mock_service.users().labels().create.assert_called_with(
            userId="me", body={"name": "new-label"}
        )
        mock_service.users().messages().modify.assert_called_with(
            userId="me",
            id="msg1",
            body={"addLabelIds": ["Label_new"]},
        )
