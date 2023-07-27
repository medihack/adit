from datetime import timedelta

import factory
from django.utils import timezone

from adit.accounts.factories import UserFactory

from .models import Token
from .utils.crypto import hash_token


class TokenFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Token
        django_get_or_create = ("token_hashed",)

    token_hashed = factory.LazyFunction(lambda: hash_token("test_token_string"))
    owner = factory.SubFactory(UserFactory)
    created_time = timezone.now()
    client = factory.Faker("word")
    expires = timezone.now() + timedelta(hours=24)
    last_used = timezone.now()
