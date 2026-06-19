from lagom import Container, dependency_definition
from sds_common.models.schema_publish_errors import SchemaPublishError

from sds_common.publishers.gcs_schema_publisher import GcsSchemaPublisher
from sds_common.publishers.github_schema_publisher import GithubSchemaPublisher
from sds_common.services.pub_sub_service import PubSubService
from sdx_base.services.storage import StorageService

from app.broadcasters.fake_broadcaster import FakeBroadcaster
from app.broadcasters.pubsub_broadcaster import PubsubBroadcaster

from app.interfaces.dataset_broadcast_interface import DatasetBroadcastInterface
from app.interfaces.dataset_deletion_repository_interface import DatasetDeletionRepositoryInterface
from app.interfaces.dataset_source_repository_interface import DatasetSourceRepositoryInterface
from app.interfaces.dataset_storage_repository_interface import DatasetStorageRepositoryInterface

from app.repositories.dataset_deletion.fake_dataset_deletion_repository import FakeDatasetDeletionRepository
from app.repositories.dataset_deletion.firestore_dataset_deletion_repository import FirestoreDatasetDeletionRepository

from app.repositories.dataset_source.bucket_dataset_source_repository import BucketDatasetSourceRepository
from app.repositories.dataset_source.fake_dataset_source_repository import FakeDatasetSourceRepository

from app.repositories.dataset_storage.fake_dataset_storage_repository import FakeDatasetStorageRepository
from app.repositories.dataset_storage.firestore_dataset_storage_repository import FirestoreDatasetStorageRepository

from app.services.schema_service import SchemaService
from app.settings import Settings


class FakePublisher:
    def __init__(self, name: str):
        self._name = name

    def publish_schema(self, file_name: str):
        print(f"Published: {file_name} to {self._name}")


class FakeErrorNotificationProtocol:
    def send_message(self, error: SchemaPublishError, topic_id: str):
        print(f"Sent fake notification for error: {error} to topic: {topic_id}")


# -------------------------
# DEV PROFILE
# Everything fake
# -------------------------


def dev(container: Container):
    container[DatasetSourceRepositoryInterface] = FakeDatasetSourceRepository

    container[DatasetStorageRepositoryInterface] = FakeDatasetStorageRepository

    container[DatasetDeletionRepositoryInterface] = FakeDatasetDeletionRepository

    container[DatasetBroadcastInterface] = FakeBroadcaster

    container[SchemaService] = SchemaService(
        bucket_publisher=FakePublisher(name="Fake bucket publisher"),
        repository_publisher=FakePublisher(name="Fake github publisher"),
        error_notification_protocol=FakeErrorNotificationProtocol(),
    )


# -------------------------
# PRODUCTION PROFILE
# Everything real
# -------------------------


def production(container: Container):
    @dependency_definition(container)
    def build_bucket_dataset_source_repository() -> BucketDatasetSourceRepository:
        return BucketDatasetSourceRepository(
            bucket_reader=StorageService(),
            settings=container[Settings],
        )

    @dependency_definition(container)
    def build_firestore_dataset_storage_repository() -> FirestoreDatasetStorageRepository:
        return FirestoreDatasetStorageRepository(
            settings=container[Settings],
        )

    @dependency_definition(container)
    def build_firestore_dataset_deletion_repository() -> FirestoreDatasetDeletionRepository:
        return FirestoreDatasetDeletionRepository(
            settings=container[Settings],
        )

    @dependency_definition(container)
    def build_pubsub_broadcaster() -> PubsubBroadcaster:
        return PubsubBroadcaster(
            settings=container[Settings],
        )

    container[DatasetSourceRepositoryInterface] = BucketDatasetSourceRepository
    container[DatasetStorageRepositoryInterface] = FirestoreDatasetStorageRepository
    container[DatasetDeletionRepositoryInterface] = FirestoreDatasetDeletionRepository
    container[DatasetBroadcastInterface] = PubsubBroadcaster
    container[SchemaService] = SchemaService(
        bucket_publisher=GcsSchemaPublisher(),
        repository_publisher=GithubSchemaPublisher(),
        error_notification_protocol=PubSubService(),
    )


# -------------------------
# local_storage_firestore
# Everything fake except FirestoreDatasetStorageRepository
# -------------------------


def local_storage_firestore(container: Container):
    @dependency_definition(container)
    def build_firestore_dataset_storage_repository() -> FirestoreDatasetStorageRepository:
        return FirestoreDatasetStorageRepository(
            settings=container[Settings],
        )

    container[DatasetSourceRepositoryInterface] = FakeDatasetSourceRepository

    container[DatasetStorageRepositoryInterface] = FirestoreDatasetStorageRepository

    container[DatasetDeletionRepositoryInterface] = FakeDatasetDeletionRepository

    container[DatasetBroadcastInterface] = FakeBroadcaster

    container[SchemaService] = SchemaService(
        bucket_publisher=FakePublisher(name="Fake bucket publisher"),
        repository_publisher=FakePublisher(name="Fake github publisher"),
        error_notification_protocol=FakeErrorNotificationProtocol(),
    )


# -------------------------
# Profile registry
# -------------------------

PROFILES = {
    "prod": production,  # Everything using production implementations
    "dev": dev,  # Everything using fake implementations
    "local_storage_firestore": local_storage_firestore,  # Everything fake except FirestoreDatasetStorageRepository
}
