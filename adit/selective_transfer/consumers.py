import asyncio
import contextlib
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from crispy_forms.utils import render_crispy_form
from django.conf import settings
from django.template.loader import render_to_string

from adit.accounts.models import User
from adit.core.utils.dicom_dataset import ResultDataset
from adit.core.utils.dicom_operator import DicomOperator

from .forms import SelectiveTransferJobForm
from .mixins import SelectiveTransferJobCreateMixin
from .utils.debounce import debounce
from .views import SELECTIVE_TRANSFER_ADVANCED_OPTIONS_COLLAPSED

logger = logging.getLogger(__name__)

lock = threading.Lock()


@contextlib.asynccontextmanager
async def async_lock(_lock):
    """To handle a thread lock in async code.

    See https://stackoverflow.com/a/63425191/166229
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _lock.acquire)
    try:
        yield  # the lock is held
    finally:
        _lock.release()


def render_error_message(message) -> str:
    return render_to_string(
        "selective_transfer/_error_message.html",
        {"error_message": str(message)},
    )


class SelectiveTransferConsumer(SelectiveTransferJobCreateMixin, AsyncJsonWebsocketConsumer):
    async def connect(self):
        logger.debug("Connected to WebSocket client.")

        self.user: User = self.scope["user"]
        self.query_operators: list[DicomOperator] = []
        self.current_message_id: int = 0
        self.pool = ThreadPoolExecutor()

        await self.accept()

    async def disconnect(self, code: int) -> None:
        self._abort_operators()
        self.pool.shutdown(wait=False, cancel_futures=True)
        logger.debug("Disconnected from WebSocket client with code: %s", code)

    async def receive_json(self, content: dict[str, Any], **kwargs) -> None:
        error_response = await self.check_permission()
        if error_response:
            await self.send(error_response)
            return

        action: str = content.get("action", "")
        if action not in ["query", "cancel", "reset", "transfer"]:
            await self.send(render_error_message(f"Invalid action to process: {action}"))
            return

        async with async_lock(lock):
            # First we abort all operators as we received a new command what to do
            self.current_message_id += 1
            message_id = self.current_message_id
            self._abort_operators()

        if action == "cancel" or action == "reset":
            # The connectors are already aborted, so we can just update the UI
            query_hint = render_to_string("selective_transfer/_query_hint.html")
            await self.send(query_hint)
            return

        # Advanced options collapsed preference is not part of the form data itself,
        # so we have to pass it separately.
        advanced_options_collapsed = self.user.preferences.get(
            SELECTIVE_TRANSFER_ADVANCED_OPTIONS_COLLAPSED, False
        )

        # We are now in a query or transfer action so we have to process the form
        form = SelectiveTransferJobForm(
            content,
            user=self.user,
            action=action,
            advanced_options_collapsed=advanced_options_collapsed,
        )
        form_valid: bool = await database_sync_to_async(form.is_valid)()

        if action == "query":
            if form_valid:
                in_progress_message = render_to_string("selective_transfer/_query_in_progress.html")
                await self.send(in_progress_message)
                asyncio.create_task(self._make_query(form, message_id))
            else:
                form_error_response = await self._build_form_error_response(
                    form, "Please correct the form errors and search again."
                )
                await self.send(form_error_response)

        elif action == "transfer":
            if form_valid:
                asyncio.create_task(self.make_transfer(form))
            else:
                form_error_response = await self._build_form_error_response(
                    form, "Please correct the form errors and transfer again."
                )
                await self.send(form_error_response)

        else:
            raise ValueError(f"Invalid action to process: {action}")

    def _abort_operators(self) -> None:
        while self.query_operators:
            for operator in self.query_operators[:]:
                self.query_operators.remove(operator)
                operator.abort()

    @database_sync_to_async
    def check_permission(self) -> str | None:
        if not self.user:
            return render_error_message("Access denied. You must be logged in.")

        if not self.user.has_perm("selective_transfer.add_selectivetransferjob"):
            return render_error_message("Access denied. You don't have the proper permission.")

        return None

    @database_sync_to_async
    def _build_form_error_response(self, form: SelectiveTransferJobForm, message: str) -> str:
        rendered_form: str = render_crispy_form(form)
        rendered_error_message: str = render_error_message(message)
        return rendered_form + rendered_error_message

    async def _make_query(self, form: SelectiveTransferJobForm, message_id: int) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.pool, self._create_and_send_query_response, form, message_id
        )

    def _create_and_send_query_response(
        self, form: SelectiveTransferJobForm, message_id: int
    ) -> None:
        with lock:
            if message_id != self.current_message_id:
                return

            operator = self.create_source_operator(form)
            self.query_operators.append(operator)

        try:
            limit = settings.SELECTIVE_TRANSFER_RESULT_LIMIT

            studies = self.query_studies(operator, form, limit)

            received_studies: list[ResultDataset] = []
            for study in studies:
                received_studies.append(study)
                max_results_reached = len(received_studies) >= limit
                if message_id == self.current_message_id:
                    self.send_query_response(form, received_studies, max_results_reached)

            if not received_studies:
                if message_id == self.current_message_id:
                    self.send_query_response(form, received_studies, False)

        except ConnectionError:
            # Ignore connection aborts (most probably from ourself)
            # Maybe we should check here if we really aborted the connection
            pass
        finally:
            with lock:
                if operator in self.query_operators:
                    self.query_operators.remove(operator)

        return None

    @debounce()
    def send_query_response(
        self,
        form: SelectiveTransferJobForm,
        studies: list[ResultDataset],
        max_results_reached: bool,
    ) -> None:
        # Rerender form to remove potential previous error messages
        rendered_form = render_crispy_form(form)

        studies = self.sort_studies(studies)

        rendered_query_results = render_to_string(
            "selective_transfer/_query_results.html",
            {
                "query": True,
                "query_results": studies,
                "max_results_reached": max_results_reached,
                "exclude_modalities": settings.EXCLUDED_MODALITIES,
            },
        )

        async_to_sync(self.send)(rendered_form + rendered_query_results)

    async def make_transfer(self, form: SelectiveTransferJobForm) -> None:
        selected_studies: str | list[str] | None = form.data.get("selected_studies")
        if selected_studies is not None:
            if isinstance(selected_studies, str):
                selected_studies = [selected_studies]
            response = await self.build_transfer_response(form, selected_studies)
            await self.send(response)

    @database_sync_to_async
    def build_transfer_response(
        self, form: SelectiveTransferJobForm, selected_studies: list[str]
    ) -> str:
        rendered_form: str = render_crispy_form(form)

        try:
            job = self.transfer_selected_studies(self.user, form, selected_studies)
        except ValueError as err:
            rendered_error_message = render_error_message(str(err))
            return rendered_form + rendered_error_message

        rendered_created_job = render_to_string(
            "selective_transfer/_created_job.html",
            {"transfer": True, "created_job": job},
        )
        return rendered_form + rendered_created_job
