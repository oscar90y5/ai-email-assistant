from django.test import TestCase
from emails.factories import EmailFactory
from emails.models import Email, EmailClassification


class EmailFactoryTestCase(TestCase):
    def test_factory_creates_persisted_email_with_defaults(self):
        email = EmailFactory()
        self.assertIsNotNone(email.pk)
        self.assertTrue(email.gmail_id.startswith("gmail_id_"))
        self.assertIsNone(email.classification)
        self.assertFalse(email.notified)
        self.assertIsNone(email.processed_at)
        self.assertEqual(Email.objects.count(), 1)

    def test_consecutive_factories_generate_unique_gmail_ids(self):
        email1 = EmailFactory()
        email2 = EmailFactory()
        self.assertNotEqual(email1.gmail_id, email2.gmail_id)

    def test_factory_with_classification(self):
        email = EmailFactory(classification=EmailClassification.IMPORTANT)
        self.assertEqual(email.classification, EmailClassification.IMPORTANT)
        retrieved = Email.objects.get(pk=email.pk)
        self.assertEqual(retrieved.classification, EmailClassification.IMPORTANT)

    def test_str_with_classification_returns_readable_label(self):
        email = EmailFactory(classification=EmailClassification.IMPORTANT, subject="Test subject", sender="test@example.com")
        self.assertIn("Important", str(email))
        self.assertIn("Test subject", str(email))
        self.assertIn("test@example.com", str(email))
