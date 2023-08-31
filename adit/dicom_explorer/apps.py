from django.apps import AppConfig
from django.db.models.signals import post_migrate

from adit.core.site import register_main_menu_item

SECTION_NAME = "DICOM Explorer"


class DicomExplorerConfig(AppConfig):
    name = "adit.dicom_explorer"

    def ready(self):
        register_app()

        # Put calls to db stuff in this signal handler
        post_migrate.connect(init_db, sender=self)


def register_app():
    register_main_menu_item(
        url_name="dicom_explorer_form",
        label=SECTION_NAME,
    )


def init_db(**kwargs):
    from shared.accounts.utils import create_group_with_permissions

    create_group_with_permissions(
        "dicom_explorer_group",
        ("dicom_explorer.query_dicom_server",),
    )
