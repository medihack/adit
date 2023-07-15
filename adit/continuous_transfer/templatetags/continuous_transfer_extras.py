from django.template import Library

from ..models import TransferTask

register = Library()


@register.inclusion_tag("core/_job_detail_control_panel.html", takes_context=True)
def job_control_panel(context):
    return {
        "delete_url": "continuous_transfer_job_delete",
        "verify_url": "continuous_transfer_job_verify",
        "cancel_url": "continuous_transfer_job_cancel",
        "resume_url": "continuous_transfer_job_resume",
        "retry_url": "continuous_transfer_job_retry",
        "restart_url": "continuous_transfer_job_restart",
        "user": context["user"],
        "job": context["job"],
    }


@register.filter
def task_status_badge_class(status):
    css_class = ""
    if status == TransferTask.Status.PENDING:
        css_class = "badge-secondary"
    elif status == TransferTask.Status.IN_PROGRESS:
        css_class = "badge-info"
    elif status == TransferTask.Status.CANCELED:
        css_class = "badge-dark"
    elif status == TransferTask.Status.SUCCESS:
        css_class = "badge-success"
    elif status == TransferTask.Status.WARNING:
        css_class = "badge-warning"
    elif status == TransferTask.Status.FAILURE:
        css_class = "badge-danger"
    return css_class
