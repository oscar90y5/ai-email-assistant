from abc import ABC, abstractmethod


class MailService(ABC):

    @abstractmethod
    def fetch_unread(self) -> list[dict]: ...

    @abstractmethod
    def mark_as_read(self, email_id: str) -> None: ...

    @abstractmethod
    def archive(self, email_id: str) -> None: ...

    @abstractmethod
    def add_label(self, email_id: str, label: str) -> None: ...
