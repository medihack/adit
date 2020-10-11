from django.apps import AppConfig
from django.db.models.signals import post_migrate
from adit.main.site import register_main_menu_item


class BatchTransferConfig(AppConfig):
    name = "adit.batch_transfer"

    def ready(self):
        register_main_menu_item(
            url_name="batch_transfer_job_create", label="Batch Transfer"
        )

        # Put calls to db stuff in this signal handler
        post_migrate.connect(init_db, sender=self)


def init_db(**kwargs):  # pylint: disable=unused-argument
    create_group()
    create_app_settings()


def create_group():
    # pylint: disable=import-outside-toplevel
    from adit.accounts.utils import create_group_with_permissions

    create_group_with_permissions(
        "batch_transferrers",
        (
            "batch_transfer.add_batchtransferjob",
            "batch_transfer.view_batchtransferjob",
        ),
    )


def create_app_settings():
    # pylint: disable=import-outside-toplevel
    from .models import AppSettings

    app_settings = AppSettings.objects.first()
    if not app_settings:
        AppSettings.objects.create()
