from typing import TYPE_CHECKING

from celery import current_app
from django.db import models
from django.urls import reverse

from adit.core.models import AppSettings, TransferJob, TransferTask
from adit.core.validators import pos_int_list_validator

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager


class BatchTransferSettings(AppSettings):
    class Meta:
        verbose_name_plural = "Batch transfer settings"


class BatchTransferJob(TransferJob):
    project_name = models.CharField(max_length=150)
    project_description = models.TextField(max_length=2000)
    ethics_application_id = models.CharField(blank=True, max_length=100)

    if TYPE_CHECKING:
        tasks = RelatedManager["BatchTransferTask"]()

    def delay(self):
        current_app.send_task("adit.batch_transfer.tasks.ProcessBatchTransferJob", (self.id,))

    def get_absolute_url(self):
        return reverse("batch_transfer_job_detail", args=[self.id])


class BatchTransferTask(TransferTask):
    job = models.ForeignKey(
        BatchTransferJob,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    lines = models.TextField(validators=[pos_int_list_validator])

    @property
    def lines_list(self) -> list[str]:
        return list(filter(len, map(str.strip, self.lines.split(","))))

    @lines_list.setter
    def lines_list(self, value: list[str]) -> None:
        self.lines = ", ".join(value)

    def get_absolute_url(self):
        return reverse("batch_transfer_task_detail", args=[self.job.id, self.task_id])
