from django.http import HttpRequest
from rest_framework.request import Request

from shared.accounts.models import User


class AuthenticatedHttpRequest(HttpRequest):
    user: User


class AuthenticatedRequest(Request):
    user: User
