from datetime import time
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericRelation
from django.urls import reverse
import celery
from adit.main.models import TransferJob, TransferTask
from adit.main.validators import validate_pseudonym


def slot_time(hour, minute):
    return time(hour, minute)


class AppSettings(models.Model):
    # Lock the batch transfer creation form
    batch_transfer_locked = models.BooleanField(default=False)
    # Suspend the batch transfer background processing.
    batch_transfer_suspended = models.BooleanField(default=False)
    # Must be set in UTC time as Celery workers can't figure out another time zone.
    # TODO It would be nicer if in Web UI the local time could be set that is
    #   converted on the fly and stored in the db as UTC. Unfortunately, this does
    #   not work with TimeField (as it is never time zone aware).
    batch_slot_begin_time = models.TimeField(
        default=slot_time(22, 0), help_text="Must be set in UTC time."
    )
    # Must be set in UTC time as Celery workers can't figure out another time zone.
    batch_slot_end_time = models.TimeField(
        default=slot_time(8, 0), help_text="Must be set in UTC time."
    )
    batch_timeout = models.IntegerField(default=3)

    @classmethod
    def load(cls):
        return cls.objects.first()

    class Meta:
        verbose_name_plural = "App settings"


class BatchTransferJob(TransferJob):
    project_name = models.CharField(max_length=150)
    project_description = models.TextField(max_length=2000)

    def job_type(self):
        return "Batch Transfer"

    def get_processed_requests(self):
        non_processed = (
            BatchTransferRequest.Status.PENDING,
            BatchTransferRequest.Status.IN_PROGRESS,
        )
        return self.requests.exclude(status__in=non_processed)

    def delay(self):
        celery.current_app.send_task(
            "adit.batch_transfer.tasks.batch_transfer", (self.id,)
        )

    def get_absolute_url(self):
        return reverse("batch_transfer_job_detail", args=[str(self.id)])


class BatchTransferRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PE", "Pending"
        IN_PROGRESS = "IP", "In Progress"
        CANCELED = "CA", "Canceled"
        SUCCESS = "SU", "Success"
        FAILURE = "FA", "Failure"

    class Meta:
        unique_together = ("row_key", "job")

    job = models.ForeignKey(
        BatchTransferJob, on_delete=models.CASCADE, related_name="requests"
    )
    transfer_tasks = GenericRelation(
        TransferTask, related_query_name="batch_transfer_request"
    )
    row_key = models.PositiveIntegerField()
    patient_id = models.CharField(null=True, blank=True, max_length=64)
    patient_name = models.CharField(null=True, blank=True, max_length=324)
    patient_birth_date = models.DateField(null=True, blank=True)
    accession_number = models.CharField(null=True, blank=True, max_length=16)
    study_date = models.DateField(null=True, blank=True)
    modality = models.CharField(null=True, blank=True, max_length=16)
    pseudonym = models.CharField(
        null=True, blank=True, max_length=64, validators=[validate_pseudonym]
    )
    status = models.CharField(
        max_length=2, choices=Status.choices, default=Status.PENDING
    )
    message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    stopped_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        errors = []

        if not (self.patient_id or self.patient_name and self.patient_birth_date):
            errors.append(
                ValidationError(
                    "A patient must be identifiable by either a PatientID "
                    "or a PatientName and PatientBirthDate."
                )
            )

        if not (self.accession_number or self.study_date and self.modality):
            errors.append(
                ValidationError(
                    "A study must be identifiable by either an AccessionNumber "
                    "or a StudyDate and Modality."
                )
            )

        if len(errors) > 0:
            raise ValidationError(errors)
