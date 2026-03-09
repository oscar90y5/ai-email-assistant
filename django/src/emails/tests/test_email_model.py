from django.test import TestCase
from emails.factories import EmailFactory
from emails.models import Email


class EmailFactoryTestCase(TestCase):
    def test_factory_creates_email_instance(self):
        email = EmailFactory()
        self.assertIsInstance(email, Email)
