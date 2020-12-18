from django.db import models
from adit.core.models import AppSettings, DicomJob, DicomTask
from adit.core.validators import (
    no_backslash_char_validator,
    no_control_chars_validator,
    no_wildcard_chars_validator,
    validate_modalities,
)


class StudiesFinderSettings(AppSettings):
    class Meta:
        verbose_name_plural = "Studies finder settings"


class StudiesFinderJob(DicomJob):
    project_name = models.CharField(max_length=150)
    project_description = models.TextField(max_length=2000)


class StudiesFinderQuery(DicomTask):
    class Meta(DicomTask.Meta):
        ordering = ("query_id",)
        unique_together = ("query_id", "job")

    query_id = models.PositiveIntegerField()
    job = models.ForeignKey(
        StudiesFinderJob, on_delete=models.CASCADE, related_name="queries"
    )
    patient_id = models.CharField(
        blank=True,
        max_length=64,
        validators=[
            no_backslash_char_validator,
            no_control_chars_validator,
            no_wildcard_chars_validator,
        ],
    )
    patient_name = models.CharField(
        blank=True,
        max_length=324,
        validators=[
            no_backslash_char_validator,
            no_control_chars_validator,
            no_wildcard_chars_validator,
        ],
    )
    patient_birth_date = models.DateField(
        null=True,
        blank=True,
        error_messages={"invalid": "Invalid date format."},
    )
    modalities = models.JSONField(
        null=True, blank=True, validators=[validate_modalities]
    )
    study_date_start = models.DateField(
        null=True,
        blank=True,
        error_messages={"invalid": "Invalid date format."},
    )
    study_date_end = models.DateField(
        null=True,
        blank=True,
        error_messages={"invalid": "Invalid date format."},
    )


class StudiesFinderResult(models.Model):
    query = models.ForeignKey(
        StudiesFinderQuery, on_delete=models.CASCADE, related_name="results"
    )
    patient_id = models.CharField(
        blank=True,
        max_length=64,
        validators=[
            no_backslash_char_validator,
            no_control_chars_validator,
            no_wildcard_chars_validator,
        ],
    )
    patient_name = models.CharField(
        blank=True,
        max_length=324,
        validators=[
            no_backslash_char_validator,
            no_control_chars_validator,
            no_wildcard_chars_validator,
        ],
    )
    patient_birth_date = models.DateField(
        null=True,
        blank=True,
        error_messages={"invalid": "Invalid date format."},
    )
    modality = models.CharField(
        blank=True,
        max_length=16,
        validators=[
            no_backslash_char_validator,
            no_control_chars_validator,
            no_wildcard_chars_validator,
        ],
    )
    study_date = models.DateField(
        null=True,
        blank=True,
        error_messages={"invalid": "Invalid date format."},
    )
    study_description = models.CharField(
        blank=True,
        max_length=64,
        validators=[
            no_backslash_char_validator,
            no_control_chars_validator,
            no_wildcard_chars_validator,
        ],
    )
    image_count = models.PositiveIntegerField()
