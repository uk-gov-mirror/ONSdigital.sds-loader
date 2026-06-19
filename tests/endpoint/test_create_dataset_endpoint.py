from fastapi import FastAPI
from starlette.testclient import TestClient

from app.factories.dataset_factories import RawDatasetFactory
from app.routes import DEPS
from app.services.dataset_service import DatasetService
from tests.conftest import MockBroadcaster


class TestCreateDatasetEndpoint:
    def test_create_dataset_first_version(
        self,
        test_app: FastAPI,
        mock_dataset_source_repo,
        mock_dataset_storage_repo,
        mock_dataset_deletion_repo,
        mock_broadcaster: MockBroadcaster,
        raw_dataset_factory: RawDatasetFactory,
    ):
        """
        Test a happy path for creating a dataset endpoint.

        - valid file in source repository
        - No other versions of this dataset exist (it will be v1)
        """

        # Use predictable survey_id and period_id
        survey_id = "123"
        period_id = "456"

        # ------------------------
        # Source repository mocks
        # ------------------------

        # Mock the source repo to return a valid JSON filename
        mock_dataset_source_repo.get_oldest_filename.return_value = "valid-filename.json"

        # Mock the source repo to return valid RawDataset
        mock_dataset_source_repo.get_raw_data.return_value = raw_dataset_factory.build(
            survey_id=survey_id,
            period_id=period_id,
        )

        # ------------------------
        # Storage repository mocks
        # ------------------------

        # Mock the current storage repository (firestore) to force version 1
        mock_dataset_storage_repo.get_latest_dataset_metadata.return_value = None

        with DEPS.override_for_test() as test_container:
            # For this test we set autodelete to True
            class MockSettings:
                autodelete_dataset: bool = True
                retain_old_datasets = False

            # Override the DatasetService dependencies with our mocks
            test_container[DatasetService] = DatasetService(
                dataset_source_repo=mock_dataset_source_repo,
                dataset_storage_repo=mock_dataset_storage_repo,
                dataset_deletion_repo=mock_dataset_deletion_repo,
                broadcaster=mock_broadcaster,
                settings=MockSettings(),
            )

            # Create a TestClient instance
            client = TestClient(test_app)

            # Make the get request to the endpoint
            response = client.get(
                "/events/dataset/create",
            )

            # Assert a 200
            assert response.status_code == 200

    def test_create_dataset_returns_200_if_source_repository_empty(
        self,
        test_app: FastAPI,
        mock_dataset_source_repo,
        mock_dataset_storage_repo,
        mock_dataset_deletion_repo,
        mock_broadcaster: MockBroadcaster,
    ):
        """
        Test that when no json files are in the source repository
        the endpoint still returns a 200 and doesn't error.

        - No files in the source repository
        """

        # ------------------------
        # Source repository mocks
        # ------------------------

        # Mock the source repo to return a None (no files)
        mock_dataset_source_repo.get_oldest_filename.return_value = None

        with DEPS.override_for_test() as test_container:
            # For this test we set autodelete to True
            class MockSettings:
                autodelete_dataset: bool = True
                retain_old_datasets = False

            # Override the DatasetService dependencies with our mocks
            test_container[DatasetService] = DatasetService(
                dataset_source_repo=mock_dataset_source_repo,
                dataset_storage_repo=mock_dataset_storage_repo,
                dataset_deletion_repo=mock_dataset_deletion_repo,
                broadcaster=mock_broadcaster,
                settings=MockSettings(),
            )

            # Create a TestClient instance
            client = TestClient(test_app)

            # Make the get request to the endpoint
            response = client.get(
                "/events/dataset/create",
            )

            # Assert a 200
            assert response.status_code == 200

    def test_create_dataset_returns_500_if_the_filename_is_invalid(
        self,
        test_app: FastAPI,
        mock_dataset_source_repo,
        mock_dataset_storage_repo,
        mock_dataset_deletion_repo,
        mock_broadcaster: MockBroadcaster,
    ):
        """
        Test that when the oldest file in the source repository
        has an invalid filename, a status 500 code is returned.

        - invalid filename in source repository
        """

        # ------------------------
        # Source repository mocks
        # ------------------------

        # Mock the source repo to return an invalid filename
        mock_dataset_source_repo.get_oldest_filename.return_value = "invalid"

        with DEPS.override_for_test() as test_container:
            # For this test we set autodelete to True
            class MockSettings:
                autodelete_dataset: bool = True
                retain_old_datasets = False

            # Override the DatasetService dependencies with our mocks
            test_container[DatasetService] = DatasetService(
                dataset_source_repo=mock_dataset_source_repo,
                dataset_storage_repo=mock_dataset_storage_repo,
                dataset_deletion_repo=mock_dataset_deletion_repo,
                broadcaster=mock_broadcaster,
                settings=MockSettings(),
            )

            # Create a TestClient instance
            client = TestClient(test_app)

            # Make the get request to the endpoint
            response = client.get(
                "/events/dataset/create",
            )

            # Assert a 500
            assert response.status_code == 500

    def test_create_dataset_returns_500_if_the_broadcast_fails(
        self,
        test_app: FastAPI,
        mock_dataset_source_repo,
        mock_dataset_storage_repo,
        mock_dataset_deletion_repo,
        mock_broadcaster: MockBroadcaster,
        raw_dataset_factory: RawDatasetFactory,
    ):
        """
        Test that when the broadcast fails, a 500 error code is returned.
        """

        # Mock the broadcaster to raise an exception
        mock_broadcaster.broadcast = lambda: Exception("Error broadcasting")

        # Use predictable survey_id and period_id
        survey_id = "123"
        period_id = "456"

        # ------------------------
        # Source repository mocks
        # ------------------------

        # Mock the source repo to return a valid JSON filename
        mock_dataset_source_repo.get_oldest_filename.return_value = "valid-filename.json"

        # Mock the source repo to return valid RawDataset
        mock_dataset_source_repo.get_raw_data.return_value = raw_dataset_factory.build(
            survey_id=survey_id,
            period_id=period_id,
        )

        # ------------------------
        # Storage repository mocks
        # ------------------------

        # Mock the current storage repository (firestore) to force version 1
        mock_dataset_storage_repo.get_latest_dataset_metadata.return_value = None

        with DEPS.override_for_test() as test_container:
            # For this test we set autodelete to True
            class MockSettings:
                autodelete_dataset: bool = True
                retain_old_datasets = False

            # Override the DatasetService dependencies with our mocks
            test_container[DatasetService] = DatasetService(
                dataset_source_repo=mock_dataset_source_repo,
                dataset_storage_repo=mock_dataset_storage_repo,
                dataset_deletion_repo=mock_dataset_deletion_repo,
                broadcaster=mock_broadcaster,
                settings=MockSettings(),
            )

            # Create a TestClient instance
            client = TestClient(test_app)

            # Make the get request to the endpoint
            response = client.get(
                "/events/dataset/create",
            )

            # Assert a 500
            assert response.status_code == 500
