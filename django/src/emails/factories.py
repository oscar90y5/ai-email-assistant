import factory
from django.utils import timezone
from .models import Email


class EmailFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Email

    gmail_id = factory.Sequence(lambda n: f"gmail_id_{n}")
    subject = factory.Faker("sentence", nb_words=6)
    sender = factory.Faker("email")
    snippet = factory.Faker("paragraph")
    received_at = factory.LazyFunction(timezone.now)
    processed_at = None
    classification = None
    notified = False
