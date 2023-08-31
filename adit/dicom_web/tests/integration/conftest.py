import os

import pandas as pd
import pytest
from dicomweb_client import DICOMwebClient
from django.conf import settings
from django.contrib.auth.models import Group

from adit.core.utils.dicom_utils import read_dataset
from shared.accounts.factories import UserFactory
from shared.token_authentication.factories import TokenFactory

# Workaround to make playwright work with Django
# see https://github.com/microsoft/playwright-pytest/issues/29#issuecomment-731515676
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


@pytest.fixture
def user_with_token():
    user = UserFactory.create()
    token_authentication_group = Group.objects.get(name="token_authentication_group")
    user.groups.add(token_authentication_group)
    token = TokenFactory.create(owner=user)
    return user, token


@pytest.fixture
def create_dicom_web_client():
    def _create_dicom_web_client(server_url: str, ae_title: str):
        client = DICOMwebClient(
            url=f"{server_url}/dicom-web/{ae_title}",
            qido_url_prefix="qidors",
            wado_url_prefix="wadors",
            stow_url_prefix="stowrs",
            headers={"Authorization": "Token test_token_string"},
        )
        return client

    return _create_dicom_web_client


@pytest.fixture
def full_data_sheet():
    full_data_sheet_path = settings.BASE_DIR / "samples" / "full_data_sheet.xlsx"
    return pd.read_excel(full_data_sheet_path)


@pytest.fixture
def extended_data_sheet():
    extended_data_sheet_path = settings.BASE_DIR / "samples" / "extended_data_sheet.xlsx"
    return pd.read_excel(extended_data_sheet_path)


@pytest.fixture
def test_dicoms():
    test_dicoms_path = settings.BASE_DIR / "samples" / "dicoms" / "1001"
    dicoms = []
    for root, _, files in os.walk(test_dicoms_path):
        if len(files) != 0:
            try:
                dicoms.extend(
                    [read_dataset(os.path.join(root, files[i])) for i in range(len(files))]
                )
            except Exception:
                continue
    if len(dicoms) == 0:
        raise Exception("No DICOM files found in samples/dicoms")
    return dicoms
