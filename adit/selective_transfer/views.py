from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic.edit import CreateView
from django.views.generic import DetailView
from django.http import HttpResponseBadRequest
from rest_framework import generics, permissions
from adit.main.mixins import OwnerRequiredMixin
from .forms import SelectiveTransferJobForm
from .models import SelectiveTransferJob
from .serializers import SelectiveTransferJobCreateSerializer


class SelectiveTransferJobFormView(
    LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    """A view class to render the selective transfer form.

    POST (and the creation of the job) is not handled by this view because the
    job itself is created by using the REST API and an AJAX call.
    """

    template_name = "selective_transfer/selective_transfer_job_form.html"
    form_class = SelectiveTransferJobForm
    permission_required = "selective_transfer.add_selectivetransferjob"

    def post(self, request, *args, **kwargs):
        return HttpResponseBadRequest()


class SelectiveTransferJobCreateAPIView(generics.CreateAPIView):
    serializer_class = SelectiveTransferJobCreateSerializer
    queryset = SelectiveTransferJob.objects.none()  # required for permission to work
    permission_classes = (permissions.DjangoModelPermissions,)

    def perform_create(self, serializer):
        job = serializer.save(
            status=SelectiveTransferJob.Status.PENDING, created_by=self.request.user
        )
        job.delay()


class SelectiveTransferJobDetailView(
    LoginRequiredMixin, OwnerRequiredMixin, DetailView
):
    model = SelectiveTransferJob
    context_object_name = "job"
    template_name = "selective_transfer/selective_transfer_job_detail.html"
    owner_accessor = "created_by"
