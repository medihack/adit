import logging
from typing import Callable, Dict, List, Optional

from adit.core.utils.dicom_connector import DicomConnector
from adit.core.utils.dicom_utils import adit_dict_to_dicom_json

logger = logging.getLogger(__name__)


class DicomWebApi:
    """
    This class implements a wrapper of the usual DicomConnector class and extends it to
    be compatible with the DICOM Web API. It is used to query and download studies and
    series using the usual DicomConnector.
    """

    def __init__(self, connector: DicomConnector):
        self.connector = connector

    def qido_find_studies(self, query: dict, limit_results: Optional[int] = None) -> list:
        studies_list = self.connector.find_studies(query, limit_results=limit_results)
        studies = adit_dict_to_dicom_json(studies_list)
        return studies

    def qido_find_series(self, query: dict, limit_results: Optional[int] = None) -> list:
        series_list = self.connector.find_series(query, limit_results=limit_results)
        series = adit_dict_to_dicom_json(series_list)
        return series

    def wado_download_study(
        self,
        study_uid: str,
        series_list: List[Dict],
        folder_path: str,
        modifier: Optional[Callable] = None,
    ) -> None:
        for series in series_list:
            series_uid = series["SeriesInstanceUID"]

            self.wado_download_series(
                study_uid,
                series_uid,
                folder_path,
                modifier=modifier,
            )

        logger.debug("Successfully downloaded study %s to ADIT.", study_uid)

    def wado_download_series(
        self,
        study_uid: str,
        series_uid: str,
        folder_path: str,
        modifier: Optional[Callable] = None,
    ) -> None:
        self.connector.download_series(
            patient_id="",
            study_uid=study_uid,
            series_uid=series_uid,
            dest_folder=folder_path,
            modifier=modifier,
        )
