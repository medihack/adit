import pytest
from dicomweb_client import DICOMwebClient
from pydicom import Dataset

from adit.core.models import DicomServer
from adit.core.utils.auth_utils import grant_access


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_single_stow(
    dimse_orthancs,
    live_server,
    user_with_group_and_token,
    create_dicom_web_client,
    test_dicoms,
):
    _, group, token = user_with_group_and_token
    server: DicomServer = DicomServer.objects.get(ae_title="ORTHANC2")
    # We must also grant source access as we query the server after
    # the upload if the images really arrived.
    grant_access(group, server, source=True, destination=True)
    orthanc2_client: DICOMwebClient = create_dicom_web_client(
        live_server.url, server.ae_title, token
    )

    studies = orthanc2_client.search_for_studies(search_filters={"PatientID": "1001"})
    assert len(studies) == 0, "Orthanc2 should be empty."

    number_of_study_related_instances: dict[str, int] = {}
    for ds in test_dicoms("1001"):
        if ds.StudyInstanceUID not in number_of_study_related_instances:
            number_of_study_related_instances[ds.StudyInstanceUID] = 0
        orthanc2_client.store_instances([ds])
        number_of_study_related_instances[ds.StudyInstanceUID] += 1

    for k, v in number_of_study_related_instances.items():
        results = orthanc2_client.search_for_studies(search_filters={"StudyInstanceUID": k})
        assert Dataset.from_json(results[0]).NumberOfStudyRelatedInstances == v


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
def test_chunked_stow(
    dimse_orthancs,
    channels_live_server,
    user_with_group_and_token,
    create_dicom_web_client,
    test_dicoms,
):
    # When sending multiple DICOM files at once then DICOMwebClient uses a chunked transfer
    # encoding, which is not supported by live_server. We work around this by using the
    # channels_live_server which itself uses Daphne (an ASGI server) with support for
    # chunked transfer encoding in requests.

    _, group, token = user_with_group_and_token
    server: DicomServer = DicomServer.objects.get(ae_title="ORTHANC2")
    # We must also grant access as source as we query the server after
    # the upload if the images are there
    grant_access(group, server, source=True, destination=True)
    orthanc2_client: DICOMwebClient = create_dicom_web_client(
        channels_live_server.url, server.ae_title, token
    )

    studies = orthanc2_client.search_for_studies(search_filters={"PatientID": "1002"})
    assert len(studies) == 0, "Orthanc2 should be empty."

    number_of_study_related_instances: dict[str, int] = {}
    datasets: list[Dataset] = []
    for ds in test_dicoms("1002"):
        if ds.StudyInstanceUID not in number_of_study_related_instances:
            number_of_study_related_instances[ds.StudyInstanceUID] = 0
        number_of_study_related_instances[ds.StudyInstanceUID] += 1
        datasets += [ds]

    orthanc2_client.store_instances(datasets)

    for k, v in number_of_study_related_instances.items():
        results = orthanc2_client.search_for_studies(search_filters={"StudyInstanceUID": k})
        assert Dataset.from_json(results[0]).NumberOfStudyRelatedInstances == v
