import base64

from fastapi import FastAPI
from sdx_base.models.pubsub import Message, Envelope
from starlette.testclient import TestClient

from app.routes import DEPS
from app.services.schema_service import SchemaService
from tests.conftest import MockPublisher, MockErrorNotificationProtocol


class TestPublishSchemasEndpoint:
    def _encode_filenames(self, filenames: str) -> Envelope:
        """
        Helper method to encode a string of filenames into the format expected by our endpoint
        """

        # Encode the message
        encoded_data = base64.b64encode(filenames.encode("utf-8")).decode("utf-8")

        # Create a fake Message object to simulate a pubsub object
        message: Message = {
            "attributes": {},
            "data": encoded_data,
            "message_id": "",
            "publish_time": "",
        }

        # Wrap in an envelope object
        return {"message": message, "subscription": ""}

    def test_publish_schemas_to_github_with_all_valid_schemas(
        self,
        test_app: FastAPI,
        mock_repo_publisher: MockPublisher,
        mock_bucket_publisher: MockPublisher,
        mock_error_notifier: MockErrorNotificationProtocol,
    ):
        """
        Test our publish schemas endpoint (to GitHub)

        Two valid schemas
        - schemas/abc/v1.json
        - schemas/abc/v2.json

        """

        with DEPS.override_for_test() as test_container:
            # Create our own schema service to use in this app
            test_container[SchemaService] = SchemaService(
                repository_publisher=mock_repo_publisher,
                bucket_publisher=mock_bucket_publisher,
                error_notification_protocol=mock_error_notifier,
            )

            # Create fake files to simulate new added schemas sent to loader
            received_filenames = "schemas/abc/v1.json\nschemas/abc/v2.json"

            # Create a TestClient instance
            client = TestClient(test_app)

            # Make a POST request to the /events/schema/publish endpoint and specify "source" to be GitHub
            response = client.post(
                "/events/schema/publish?source=github", json=self._encode_filenames(received_filenames)
            )

            # Assert a 200 status code
            assert response.status_code == 200

            # Assert both files made it into our mock_repo_publisher
            assert len(mock_repo_publisher.published_schemas) == 2
            assert "schemas/abc/v1.json" in mock_repo_publisher.published_schemas
            assert "schemas/abc/v2.json" in mock_repo_publisher.published_schemas

            # Assert nothing made it to the mock_bucket_publisher
            assert len(mock_bucket_publisher.published_schemas) == 0

    def test_publish_schemas_to_bucket_with_all_valid_schemas(
        self,
        test_app: FastAPI,
        mock_repo_publisher: MockPublisher,
        mock_bucket_publisher: MockPublisher,
        mock_error_notifier: MockErrorNotificationProtocol,
    ):
        """
        Test our publish schemas endpoint with a single
        valid bucket path

        - gcp/ons-sdx-bob/buckets/v1.json

        """

        with DEPS.override_for_test() as test_container:
            # Create our own schema service to use in this app
            test_container[SchemaService] = SchemaService(
                repository_publisher=mock_repo_publisher,
                bucket_publisher=mock_bucket_publisher,
                error_notification_protocol=mock_error_notifier,
            )

            # Create fake files to simulate new added schemas sent to loader
            received_filenames = '{"name": "v1.json"}'

            # Create a TestClient instance
            client = TestClient(test_app)

            # Make a POST request to the /events/schema/publish endpoint and specify "source" to be bucket
            response = client.post(
                "/events/schema/publish?source=bucket", json=self._encode_filenames(received_filenames)
            )

            # Assert a 200 status code
            assert response.status_code == 200

            # Assert the file was published by the mock_bucket_publisher
            assert "v1.json" in mock_bucket_publisher.published_schemas

            # Assert the mock_repo_publisher is empty
            assert len(mock_repo_publisher.published_schemas) == 0

    def test_publish_schemas_to_github_with_some_invalid_filenames(
        self,
        test_app: FastAPI,
        mock_repo_publisher: MockPublisher,
        mock_bucket_publisher: MockPublisher,
        mock_error_notifier: MockErrorNotificationProtocol,
    ):
        """
        Test our publish schemas endpoint (to GitHub)

        Two valid schemas
        - schemas/abc/v1.json
        - schemas/abc/v3.json

        Two invalid schemas
        - other/foo/v2.json
        - other/foo/v2_template.json

        """

        with DEPS.override_for_test() as test_container:
            # Create our own schema service to use in this app
            test_container[SchemaService] = SchemaService(
                repository_publisher=mock_repo_publisher,
                bucket_publisher=mock_bucket_publisher,
                error_notification_protocol=mock_error_notifier,
            )

            # Create fake files to simulate new added schemas sent to loader
            received_filenames = (
                "schemas/abc/v1.json\nother/foo/v2.json\nschemas/abc/v3.json\nother/foo/v2_template.json"
            )

            # Create a TestClient instance
            client = TestClient(test_app)

            # Make a POST request to the /events/schema/publish endpoint and specify "source" to be GitHub
            response = client.post(
                "/events/schema/publish?source=github", json=self._encode_filenames(received_filenames)
            )

            # Assert a 200 status code
            assert response.status_code == 200

            # Assert both files made it into our mock_repo_publisher
            assert len(mock_repo_publisher.published_schemas) == 2
            assert "schemas/abc/v1.json" in mock_repo_publisher.published_schemas
            assert "schemas/abc/v3.json" in mock_repo_publisher.published_schemas

            # Assert nothing made it to the mock_bucket_publisher
            assert len(mock_bucket_publisher.published_schemas) == 0
