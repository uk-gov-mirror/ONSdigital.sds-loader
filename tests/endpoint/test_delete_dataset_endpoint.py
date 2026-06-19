from fastapi import FastAPI
from starlette.testclient import TestClient

from app.routes import DEPS
from app.services.dataset_service import DatasetService
from tests.conftest import MockBroadcaster


class TestDeleteDatasetEndpoint:
    def test_returns_200_when_no_datasets_are_to_be_deleted(
        self,
        test_app: FastAPI,
        mock_dataset_source_repo,
        mock_dataset_storage_repo,
        mock_dataset_deletion_repo,
        mock_broadcaster: MockBroadcaster,
    ):
        """
        Test that when we call the delete dataset endpoint,
        but no datasets are marked to delete, the process completes successfully and returns a 200 status code.
        """

        # ------------------------
        # Dataset deletion repository mocks
        # ------------------------

        # Mock the dataset deletion repository to return a None (no datasets marked for deletion)
        mock_dataset_deletion_repo.get_dataset_to_delete.return_value = None

        with DEPS.override_for_test() as test_container:
            # For this test we set autodelete to True
            class MockSettings:
                autodelete_dataset: bool = False
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
                "/events/dataset/delete",
            )

            # Assert a 200
            assert response.status_code == 200

    def test_returns_500_when_an_error_occurs_during_dataset_deletion(
        self,
        test_app: FastAPI,
        mock_dataset_source_repo,
        mock_dataset_storage_repo,
        mock_dataset_deletion_repo,
        mock_broadcaster: MockBroadcaster,
    ):
        """
        Test that when an error occurs during dataset deletion,
        a 500 status code is returned.
        """

        # ------------------------
        # Dataset deletion repository mocks
        # ------------------------

        # Mock the dataset deletion repository to return a valid Guid ready for deletion
        mock_dataset_deletion_repo.get_dataset_to_delete.return_value = "123"

        # ------------------------
        # Dataset storage repository mocks
        # ------------------------

        def error():
            raise Exception("Problem")

        # Mock the delete method to throw some sort of error
        mock_dataset_storage_repo.delete_dataset_by_guid.side_effect = error

        with DEPS.override_for_test() as test_container:
            # For this test we set autodelete to True
            class MockSettings:
                autodelete_dataset: bool = False
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
                "/events/dataset/delete",
            )

            # Assert a 500
            assert response.status_code == 500
