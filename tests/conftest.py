import os
from typing import Callable
from unittest.mock import create_autospec

import pytest
from fastapi import FastAPI
from polyfactory.pytest_plugin import register_fixture
from sds_common.models.schema_publish_errors import SchemaPublishError
from sdx_base.run import initialise
from sdx_base.server.server import RouterConfig
from sdx_base.server.tx_id import txid_not_applicable
from sdx_base.settings.app import AppSettings

from app.factories.dataset_factories import RawDatasetFactory, DatasetMetadataWithoutIdFactory
from app.interfaces.dataset_broadcast_interface import DatasetBroadcastInterface
from app.interfaces.dataset_deletion_repository_interface import DatasetDeletionRepositoryInterface
from app.interfaces.dataset_source_repository_interface import DatasetSourceRepositoryInterface
from app.interfaces.dataset_storage_repository_interface import DatasetStorageRepositoryInterface
from app.models.dataset import DatasetMetadata
from app.routes import router
from app.settings import ROOT

# ------------------------
# Factories
# ------------------------

# Register RawDatasetFactory with pytest
register_fixture(RawDatasetFactory)
register_fixture(DatasetMetadataWithoutIdFactory)

# ------------------------
# Testing classes for schema_service
# ------------------------


class MockPublisher:
    """
    Mock Publisher class, allows
    tracking of published schemas and side effects for testing purposes.
    """

    def __init__(self, label: str):
        self.label = label
        self.side_effects = {}
        self.published_schemas = []

    def add_side_effect(self, file_name: str, side_effect: Callable):
        self.side_effects[file_name] = side_effect

    def publish_schema(self, file_name: str):
        if file_name in self.side_effects:
            try:
                self.side_effects[file_name]()
            except Exception as e:
                print(e)
                raise e

        self.published_schemas.append(file_name)


class MockErrorNotificationProtocol:
    def __init__(self):
        self.sent_notifications = []

    def send_message(self, error: SchemaPublishError, topic_id: str):
        print(f"Sent fake notification for error: {error} to topic: {topic_id}")
        self.sent_notifications.append([topic_id, error])


# ------------------------
# Testing classes for dataset_service
# ------------------------


class MockBroadcaster(DatasetBroadcastInterface):
    """
    A mock broadcaster for testing the broadcasting of dataset metadata.
    """

    def __init__(self):
        self.broadcasted_datasets = []

    def broadcast(self, dataset_metadata: DatasetMetadata) -> None:
        self.broadcasted_datasets.append(dataset_metadata)


# ------------------------
# Fixtures for schema_service
# ------------------------


@pytest.fixture
def mock_repo_publisher() -> MockPublisher:
    return MockPublisher(label="repo publisher")


@pytest.fixture
def mock_bucket_publisher() -> MockPublisher:
    return MockPublisher(
        label="bucket publisher",
    )


@pytest.fixture
def mock_error_notifier() -> MockErrorNotificationProtocol:
    return MockErrorNotificationProtocol()


# ------------------------
# Fixtures for dataset_service
# ------------------------


@pytest.fixture
def mock_dataset_source_repo() -> DatasetSourceRepositoryInterface:
    return create_autospec(DatasetSourceRepositoryInterface)


@pytest.fixture
def mock_dataset_deletion_repo() -> DatasetDeletionRepositoryInterface:
    return create_autospec(DatasetDeletionRepositoryInterface)


@pytest.fixture
def mock_dataset_storage_repo() -> DatasetStorageRepositoryInterface:
    return create_autospec(DatasetStorageRepositoryInterface)


@pytest.fixture
def mock_broadcaster() -> DatasetBroadcastInterface:
    return MockBroadcaster()


# ------------------------
# App fixture
# ------------------------


@pytest.fixture
def test_app() -> FastAPI:
    """
    This fixture will create a FastAPI app using SDX base
    """

    # Set environment variable for testing
    os.environ["PROJECT_ID"] = "ons-sdx-sandbox"

    # Fake Settings
    class FakeSettings(AppSettings):
        project_id: str

    class MockSecretReader:
        def get_secret(self, project_id: str, secret_id: str) -> str:
            return "secret"

    return initialise(
        settings=FakeSettings,
        routers=[RouterConfig(router, tx_id_getter=txid_not_applicable)],
        proj_root=ROOT,
        secret_reader=MockSecretReader,
    )
