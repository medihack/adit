from unittest.mock import create_autospec, patch
import pytest
from pydicom.dataset import Dataset
from pynetdicom import Association
from pynetdicom.status import Status
from pynetdicom.sop_class import (  # pylint: disable-msg=no-name-in-module
    PatientRootQueryRetrieveInformationModelFind,
    PatientRootQueryRetrieveInformationModelGet,
    PatientRootQueryRetrieveInformationModelMove,
    StudyRootQueryRetrieveInformationModelFind,
    StudyRootQueryRetrieveInformationModelGet,
    StudyRootQueryRetrieveInformationModelMove,
)
from adit.core.utils.dicom_connector import DicomConnector


class DicomTestHelper:
    @staticmethod
    def create_dataset_from_dict(data):
        ds = Dataset()
        for i in data:
            setattr(ds, i, data[i])
        return ds

    @staticmethod
    def create_c_find_responses(data_dicts):
        responses = []
        for data_dict in data_dicts:
            identifier = DicomTestHelper.create_dataset_from_dict(data_dict)
            pending_status = Dataset()
            pending_status.Status = Status.PENDING
            responses.append((pending_status, identifier))

        success_status = Dataset()
        success_status.Status = Status.SUCCESS
        responses.append((success_status, None))

        return responses

    @staticmethod
    def create_c_get_responses():
        responses = []
        success_status = Dataset()
        success_status.Status = Status.SUCCESS
        responses.append((success_status, None))
        return responses

    @staticmethod
    def create_c_store_response():
        success_status = Dataset()
        success_status.Status = Status.SUCCESS
        return success_status


@pytest.fixture
def dicom_test_helper():
    return DicomTestHelper


@pytest.fixture
def association():
    assoc = create_autospec(Association)
    assoc.is_established = True
    return assoc


@pytest.fixture
def dicom_connector():
    config = DicomConnector.Config(
        client_ae_title="CLIENT_AE_TITLE",
        server_ae_title="SERVER_AE_TITLE",
        server_host="127.0.0.1",
        server_port=104,
    )
    return DicomConnector(config)


@patch("adit.core.utils.dicom_connector.AE.associate")
def test_find_patients(
    associate, association, dicom_connector, dicom_test_helper: DicomTestHelper
):
    # Arrange
    associate.return_value = association
    responses = [{"PatientName": "Foo^Bar", "PatientID": "1001"}]
    association.send_c_find.return_value = dicom_test_helper.create_c_find_responses(
        responses
    )
    # Act
    patients = dicom_connector.find_patients({"PatientName": "Foo^Bar"})
    # Assert
    association.send_c_find.assert_called_once()
    assert isinstance(association.send_c_find.call_args.args[0], Dataset)
    assert patients[0]["PatientID"] == responses[0]["PatientID"]
    assert (
        association.send_c_find.call_args.args[1]
        == PatientRootQueryRetrieveInformationModelFind
    )


@patch("adit.core.utils.dicom_connector.AE.associate")
def test_find_studies_with_patient_root(
    associate,
    association,
    dicom_connector: DicomConnector,
    dicom_test_helper: DicomTestHelper,
):
    # Arrange
    associate.return_value = association
    responses = [{"PatientID": "12345"}]
    association.send_c_find.return_value = dicom_test_helper.create_c_find_responses(
        responses
    )
    # Act
    patients = dicom_connector.find_studies({"PatientID": "12345"})
    # Assert
    association.send_c_find.assert_called_once()
    assert isinstance(association.send_c_find.call_args.args[0], Dataset)
    assert patients[0]["PatientID"] == responses[0]["PatientID"]
    assert (
        association.send_c_find.call_args.args[1]
        == PatientRootQueryRetrieveInformationModelFind
    )


@patch("adit.core.utils.dicom_connector.AE.associate")
def test_find_studies_with_study_root(
    associate,
    association,
    dicom_connector: DicomConnector,
    dicom_test_helper: DicomTestHelper,
):
    # Arrange
    associate.return_value = association
    responses = [{"PatientName": "Foo^Bar"}]
    association.send_c_find.return_value = dicom_test_helper.create_c_find_responses(
        responses
    )
    # Act
    patients = dicom_connector.find_studies({"PatientName": "Foo^Bar"}, study_root=True)
    # Assert
    association.send_c_find.assert_called_once()
    assert isinstance(association.send_c_find.call_args.args[0], Dataset)
    assert patients[0]["PatientName"] == responses[0]["PatientName"]
    assert (
        association.send_c_find.call_args.args[1]
        == StudyRootQueryRetrieveInformationModelFind
    )


@patch("adit.core.utils.dicom_connector.AE.associate")
def test_find_series(
    associate,
    association,
    dicom_connector: DicomConnector,
    dicom_test_helper: DicomTestHelper,
):
    # Arrange
    associate.return_value = association
    responses = [{"PatientID": "12345", "StudyInstanceUID": "1.123"}]
    association.send_c_find.return_value = dicom_test_helper.create_c_find_responses(
        responses
    )
    # Act
    patients = dicom_connector.find_series(
        {"PatientID": "12345", "StudyInstanceUID": "1.123"}
    )
    # Assert
    association.send_c_find.assert_called_once()
    assert isinstance(association.send_c_find.call_args.args[0], Dataset)
    assert patients[0]["PatientID"] == responses[0]["PatientID"]
    assert (
        association.send_c_find.call_args.args[1]
        == PatientRootQueryRetrieveInformationModelFind
    )
