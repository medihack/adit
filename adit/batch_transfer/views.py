from typing import Any

from django.conf import settings
from django.urls import reverse_lazy

from adit.core.views import (
    BaseUpdatePreferencesView,
    DicomJobCancelView,
    DicomJobCreateView,
    DicomJobDeleteView,
    DicomJobDetailView,
    DicomJobRestartView,
    DicomJobResumeView,
    DicomJobRetryView,
    DicomJobVerifyView,
    DicomTaskDetailView,
    TransferJobListView,
)

from .filters import BatchTransferJobFilter, BatchTransferTaskFilter
from .forms import BatchTransferJobForm
from .mixins import BatchTransferLockedMixin
from .models import BatchTransferJob, BatchTransferTask
from .tables import BatchTransferJobTable, BatchTransferTaskTable

BATCH_TRANSFER_SOURCE = "batch_transfer_source"
BATCH_TRANSFER_DESTINATION = "batch_transfer_destination"
BATCH_TRANSFER_URGENT = "batch_transfer_urgent"
BATCH_TRANSFER_SEND_FINISHED_MAIL = "batch_transfer_send_finished_mail"


class BatchTransferUpdatePreferencesView(BatchTransferLockedMixin, BaseUpdatePreferencesView):
    allowed_keys = [
        BATCH_TRANSFER_SOURCE,
        BATCH_TRANSFER_DESTINATION,
        BATCH_TRANSFER_URGENT,
        BATCH_TRANSFER_SEND_FINISHED_MAIL,
    ]


class BatchTransferJobListView(BatchTransferLockedMixin, TransferJobListView):
    model = BatchTransferJob
    table_class = BatchTransferJobTable
    filterset_class = BatchTransferJobFilter
    template_name = "batch_transfer/batch_transfer_job_list.html"


class BatchTransferJobCreateView(BatchTransferLockedMixin, DicomJobCreateView):
    model = BatchTransferJob
    form_class = BatchTransferJobForm
    template_name = "batch_transfer/batch_transfer_job_form.html"
    permission_required = "batch_transfer.add_batchtransferjob"
    default_priority = settings.BATCH_TRANSFER_DEFAULT_PRIORITY
    urgent_priority = settings.BATCH_TRANSFER_URGENT_PRIORITY
    object: BatchTransferJob

    def get_initial(self) -> dict[str, Any]:
        initial = super().get_initial()

        preferences: dict[str, Any] = self.request.user.preferences

        source = preferences.get(BATCH_TRANSFER_SOURCE)
        if source is not None:
            initial["source"] = source

        destination = preferences.get(BATCH_TRANSFER_DESTINATION)
        if destination is not None:
            initial["destination"] = destination

        urgent = preferences.get(BATCH_TRANSFER_URGENT)
        if urgent is not None:
            initial["urgent"] = urgent

        send_finished_mail = preferences.get(BATCH_TRANSFER_SEND_FINISHED_MAIL)
        if send_finished_mail is not None:
            initial["send_finished_mail"] = send_finished_mail

        return initial

    def form_valid(self, form):
        return super().form_valid(form, settings.BATCH_TRANSFER_UNVERIFIED)


class BatchTransferJobDetailView(BatchTransferLockedMixin, DicomJobDetailView):
    table_class = BatchTransferTaskTable
    filterset_class = BatchTransferTaskFilter
    model = BatchTransferJob
    context_object_name = "job"
    template_name = "batch_transfer/batch_transfer_job_detail.html"


class BatchTransferJobDeleteView(BatchTransferLockedMixin, DicomJobDeleteView):
    model = BatchTransferJob
    success_url = reverse_lazy("batch_transfer_job_list")


class BatchTransferJobVerifyView(BatchTransferLockedMixin, DicomJobVerifyView):
    model = BatchTransferJob
    default_priority = settings.BATCH_TRANSFER_DEFAULT_PRIORITY
    urgent_priority = settings.BATCH_TRANSFER_URGENT_PRIORITY


class BatchTransferJobCancelView(BatchTransferLockedMixin, DicomJobCancelView):
    model = BatchTransferJob


class BatchTransferJobResumeView(BatchTransferLockedMixin, DicomJobResumeView):
    model = BatchTransferJob
    default_priority = settings.BATCH_TRANSFER_DEFAULT_PRIORITY
    urgent_priority = settings.BATCH_TRANSFER_URGENT_PRIORITY


class BatchTransferJobRetryView(BatchTransferLockedMixin, DicomJobRetryView):
    model = BatchTransferJob
    default_priority = settings.BATCH_TRANSFER_DEFAULT_PRIORITY
    urgent_priority = settings.BATCH_TRANSFER_URGENT_PRIORITY


class BatchTransferJobRestartView(BatchTransferLockedMixin, DicomJobRestartView):
    model = BatchTransferJob
    default_priority = settings.BATCH_TRANSFER_DEFAULT_PRIORITY
    urgent_priority = settings.BATCH_TRANSFER_URGENT_PRIORITY


class BatchTransferTaskDetailView(BatchTransferLockedMixin, DicomTaskDetailView):
    model = BatchTransferTask
    job_url_name = "batch_transfer_job_detail"
    template_name = "batch_transfer/batch_transfer_task_detail.html"
