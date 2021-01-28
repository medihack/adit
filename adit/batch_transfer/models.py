from django.db import models
from django.urls import reverse
from adit.core.models import AppSettings, TransferJob, TransferTask


class BatchTransferSettings(AppSettings):
    class Meta:
        verbose_name_plural = "Batch transfer settings"


class BatchTransferJob(TransferJob):
    project_name = models.CharField(max_length=150)
    project_description = models.TextField(max_length=2000)

    def delay(self):
        # pylint: disable=import-outside-toplevel
        from .tasks import process_transfer_job

        process_transfer_job.delay(self.id)

    def get_absolute_url(self):
        return reverse("batch_transfer_job_detail", args=[self.id])


class BatchTransferTask(TransferTask):
    job = models.ForeignKey(
        BatchTransferJob,
        on_delete=models.CASCADE,
        related_name="tasks",
    )

    def get_absolute_url(self):
        return reverse("batch_transfer_task_detail", args=[self.job.id, self.task_id])
