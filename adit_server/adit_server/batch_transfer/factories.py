import factory
from faker import Faker

from adit_server.core.factories import (
    AbstractTransferJobFactory,
    AbstractTransferTaskFactory,
)

from .models import BatchTransferJob, BatchTransferTask

fake = Faker()


class BatchTransferJobFactory(AbstractTransferJobFactory[BatchTransferJob]):
    class Meta:
        model = BatchTransferJob

    project_name = factory.Faker("sentence")
    project_description = factory.Faker("paragraph")


class BatchTransferTaskFactory(AbstractTransferTaskFactory[BatchTransferTask]):
    class Meta:
        model = BatchTransferTask

    job = factory.SubFactory(BatchTransferJobFactory)
    lines = factory.LazyFunction(lambda: [fake.pyint(min_value=2)])
