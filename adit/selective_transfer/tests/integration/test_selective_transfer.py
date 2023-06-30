from typing import Callable

import pytest
from playwright.sync_api import Locator, Page, expect

from adit.selective_transfer.models import SelectiveTransferJob


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_unpseudonymized_urgent_selective_transfer(
    page: Page,
    poll: Callable[[Locator], Locator],
    setup_orthancs,
    adit_celery_worker,
    channels_live_server,
    create_and_login_user,
):
    user = create_and_login_user(channels_live_server.url)
    user.join_group("selective_transfer_group")
    user.add_permission("can_process_urgently", SelectiveTransferJob)
    user.add_permission("can_transfer_unpseudonymized", SelectiveTransferJob)

    page.goto(channels_live_server.url + "/selective-transfer/jobs/new/")
    page.get_by_label("Start transfer directly").click(force=True)
    page.get_by_label("Source").select_option(label="DICOM Server Orthanc Test Server 1")
    page.get_by_label("Destination").select_option(label="DICOM Server Orthanc Test Server 2")
    page.get_by_label("Patient ID").press("Enter")
    page.locator('tr:has-text("1008"):has-text("2020") input').click()
    page.locator('button:has-text("Start transfer")').click()
    page.locator('a:has-text("ID")').click()

    expect(poll(page.locator('dl:has-text("Success")'))).to_be_visible()


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_pseudonymized_urgent_selective_transfer_dicomweb(
    page: Page,
    poll: Callable[[Locator], Locator],
    setup_dicomweb_orthancs,
    adit_celery_worker,
    channels_live_server,
    create_and_login_user,
):
    user = create_and_login_user(channels_live_server.url)
    user.join_group("selective_transfer_group")
    user.add_permission("can_process_urgently", SelectiveTransferJob)
    user.add_permission("can_transfer_unpseudonymized", SelectiveTransferJob)

    page.goto(channels_live_server.url + "/selective-transfer/jobs/new/")
    page.get_by_label("Start transfer directly").click(force=True)
    page.get_by_label("Source").select_option(label="DICOM Server Orthanc Test Server 1")
    page.get_by_label("Destination").select_option(label="DICOM Server Orthanc Test Server 2")
    page.get_by_label("Patient ID").press("Enter")
    page.locator('tr:has-text("1008"):has-text("2020") input').click()
    page.locator('button:has-text("Start transfer")').click()
    page.locator('a:has-text("ID")').click()

    expect(poll(page.locator('dl:has-text("Success")'))).to_be_visible()
