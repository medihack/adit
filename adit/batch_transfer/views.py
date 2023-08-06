from typing import Any

from django.conf import settings
from django.urls import reverse_lazy
from django.views.generic import TemplateView

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
from .models import BatchTransferJob, BatchTransferSettings, BatchTransferTask
from .tables import BatchTransferJobTable, BatchTransferTaskTable

BATCH_TRANSFER_SOURCE = "batch_transfer_source"
BATCH_TRANSFER_DESTINATION = "batch_transfer_destination"
BATCH_TRANSFER_URGENT = "batch_transfer_urgent"
BATCH_TRANSFER_SEND_FINISHED_MAIL = "batch_transfer_send_finished_mail"


class BatchTransferUpdatePreferencesView(BaseUpdatePreferencesView):
    allowed_keys = [
        BATCH_TRANSFER_SOURCE,
        BATCH_TRANSFER_DESTINATION,
        BATCH_TRANSFER_URGENT,
        BATCH_TRANSFER_SEND_FINISHED_MAIL,
    ]


class BatchTransferJobListView(TransferJobListView):
    model = BatchTransferJob
    table_class = BatchTransferJobTable
    filterset_class = BatchTransferJobFilter
    template_name = "batch_transfer/batch_transfer_job_list.html"


class BatchTransferJobCreateView(DicomJobCreateView):
    model = BatchTransferJob
    form_class = BatchTransferJobForm
    template_name = "batch_transfer/batch_transfer_job_form.html"
    permission_required = "batch_transfer.add_batchtransferjob"
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
        user = self.request.user
        form.instance.owner = user
        response = super().form_valid(form)

        # Do it after an ongoing transaction (even if it is currently
        # unnecessary as ATOMIC_REQUESTS is False), see also
        # https://spapas.github.io/2019/02/25/django-fix-async-db/
        # Currently I am not using it because it is hard to test, but there
        # it is already fixed in an upcoming release, see
        # https://code.djangoproject.com/ticket/30457
        # TODO transaction.on_commit(lambda: enqueue_batch_job(self.object.id))
        job = self.object  # set by super().form_valid(form)
        if user.is_staff or settings.BATCH_TRANSFER_UNVERIFIED:
            job.status = BatchTransferJob.Status.PENDING
            job.save()
            job.delay()

        return response

    def dispatch(self, request, *args, **kwargs):
        batch_transfer_settings = BatchTransferSettings.get()
        assert batch_transfer_settings

        if batch_transfer_settings.locked and not self.request.user.is_staff:
            return TemplateView.as_view(template_name="batch_transfer/batch_transfer_locked.html")(
                request
            )
        return super().dispatch(request, *args, **kwargs)


class BatchTransferJobDetailView(DicomJobDetailView):
    table_class = BatchTransferTaskTable
    filterset_class = BatchTransferTaskFilter
    model = BatchTransferJob
    context_object_name = "job"
    template_name = "batch_transfer/batch_transfer_job_detail.html"


class BatchTransferJobDeleteView(DicomJobDeleteView):
    model = BatchTransferJob
    success_url = reverse_lazy("batch_transfer_job_list")


class BatchTransferJobVerifyView(DicomJobVerifyView):
    model = BatchTransferJob


class BatchTransferJobCancelView(DicomJobCancelView):
    model = BatchTransferJob


class BatchTransferJobResumeView(DicomJobResumeView):
    model = BatchTransferJob


class BatchTransferJobRetryView(DicomJobRetryView):
    model = BatchTransferJob


class BatchTransferJobRestartView(DicomJobRestartView):
    model = BatchTransferJob


class BatchTransferTaskDetailView(DicomTaskDetailView):
    model = BatchTransferTask
    job_url_name = "batch_transfer_job_detail"
    template_name = "batch_transfer/batch_transfer_task_detail.html"
