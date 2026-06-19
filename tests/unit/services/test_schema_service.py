from sds_common.models.schema_publish_errors import SchemaDuplicationError

from app.services.schema_service import SchemaService
from tests.conftest import MockPublisher, MockErrorNotificationProtocol


def raise_schema_error():
    """
    Raise SchemaDuplicationError. which inherits from SchemaPublishError.
    """
    raise SchemaDuplicationError("error")


class TestPublishNewSchemas:
    def test_publish_new_schemas_publishes_after_exception(
        self,
        mock_repo_publisher: MockPublisher,
        mock_bucket_publisher: MockPublisher,
        mock_error_notifier: MockErrorNotificationProtocol,
    ):
        # Define input filenames
        filenames = [
            "schemas/abc/v1.json",
            "schemas/abc/v2.json",  # This one will raise a schema exception
            "schemas/abc/v3.json",
            "schemas/abc/v4.json",
        ]

        # Add the side effect to cause v2 to fail
        mock_repo_publisher.add_side_effect("schemas/abc/v2.json", raise_schema_error)

        # Create a SchemaService
        service = SchemaService(
            repository_publisher=mock_repo_publisher,
            bucket_publisher=mock_bucket_publisher,
            error_notification_protocol=mock_error_notifier,
        )

        # Publish schemas from GitHub
        service.publish_new_schemas("github", filenames)

        should_be_published = [
            "schemas/abc/v1.json",
            "schemas/abc/v3.json",
            "schemas/abc/v4.json",
        ]

        # Assert length of published is correct
        assert len(mock_repo_publisher.published_schemas) == len(should_be_published)

        # Check each file has been published by the GitHub publisher
        for filename in should_be_published:
            assert filename in mock_repo_publisher.published_schemas

        # Assert the bucket publisher is empty
        assert mock_bucket_publisher.published_schemas == []

        # Assert the mock_error_notifier was called for the schema that raised an exception
        assert len(mock_error_notifier.sent_notifications) == 1

    def test_publish_all_files_successfully(
        self,
        mock_repo_publisher: MockPublisher,
        mock_bucket_publisher: MockPublisher,
        mock_error_notifier: MockErrorNotificationProtocol,
    ):
        # Define input filenames
        repo_filenames = [
            "schemas/abc/v1.json",
            "schemas/abc/v2.json",
            "schemas/abc/v3.json",
            "schemas/abc/v4.json",
        ]

        bucket_filenames = [
            "gcp/project/v1.json",
            "gcp/project/v2.json",
            "gcp2/project2/v1.json",
        ]

        # Create a SchemaService
        service = SchemaService(
            repository_publisher=mock_repo_publisher,
            bucket_publisher=mock_bucket_publisher,
            error_notification_protocol=mock_error_notifier,
        )

        # Publish the repository filenames
        service.publish_new_schemas("github", repo_filenames)

        # Publish the bucket filenames
        service.publish_new_schemas("bucket", bucket_filenames)

        # Assert all the GitHub files are published
        assert len(mock_repo_publisher.published_schemas) == len(repo_filenames)
        for filename in repo_filenames:
            assert filename in mock_repo_publisher.published_schemas

        # Assert the bucket publisher files are published
        assert len(mock_bucket_publisher.published_schemas) == len(bucket_filenames)
        for filename in bucket_filenames:
            assert filename in mock_bucket_publisher.published_schemas

    def test_publish_github_filter(
        self,
        mock_repo_publisher: MockPublisher,
        mock_bucket_publisher: MockPublisher,
        mock_error_notifier: MockErrorNotificationProtocol,
    ):
        """
        TODO this can probably be refactored
        """

        filenames = {
            "schemas/a/b.json": True,
            "schemas/abc/def.json": True,
            "schemas/a/b.JSON": False,  # case-sensitive
            "schemas/a/b": False,  # no extension
            "schemas/a/b.json/extra": False,  # too deep
            "schemas/a//b.json": False,  # empty segment => doesn't match [^/]+
            "schemas//b.json": False,  # empty segment
            "schemas/a/": False,  # missing filename
            "Schemas/a/b.json": False,  # wrong case in prefix
            "other/schemas/a/b.json": False,  # doesn't start with schemas/
        }

        service = SchemaService(
            repository_publisher=mock_repo_publisher,
            bucket_publisher=mock_bucket_publisher,
            error_notification_protocol=mock_error_notifier,
        )

        service.publish_new_schemas("github", list(filenames.keys()))

        # Assert only the valid filenames are published
        assert len(mock_repo_publisher.published_schemas) == 2
        assert "schemas/a/b.json" in mock_repo_publisher.published_schemas
        assert "schemas/abc/def.json" in mock_repo_publisher.published_schemas
