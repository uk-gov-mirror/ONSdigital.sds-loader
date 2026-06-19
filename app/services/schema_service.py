import re
from typing import Protocol

from sds_common.config.config import CONFIG
from sds_common.models.schema_publish_errors import SchemaPublishError

from app import get_logger
from app.exceptions.schema_source_invalid_exception import SchemaSourceInvalidException

logger = get_logger()


class PublisherProtocol(Protocol):
    """
    This protocol defines the interface for a schema publisher
    which is responsible for publishing schema files.
    """

    def publish_schema(self, file_name: str): ...


class ErrorNotificationProtocol(Protocol):
    """
    This protocol defines the interface for sending a notification
    when an error occurs
    """

    def send_message(self, error: SchemaPublishError, topic_id: str): ...


class SchemaService:
    """
    SchemaService provides a way to publish new schema files.
    """

    def __init__(
        self,
        bucket_publisher: PublisherProtocol,
        repository_publisher: PublisherProtocol,
        error_notification_protocol: ErrorNotificationProtocol,
    ):
        self.bucket_publisher = bucket_publisher
        self.repository_publisher = repository_publisher
        self.error_notification_protocol = error_notification_protocol

    def _publish_single_file(self, file_name: str, publisher: PublisherProtocol):  # noqa
        """
        Publish a single file using a given publisher
        :param file_name: name of the file to be published
        :param publisher: publisher - the publishing protocol to use to publish the file
        """

        logger.info(f"Starting publishing schema {file_name}")
        try:
            publisher.publish_schema(file_name=file_name)
            logger.info(f"Successfully published schema: {file_name}")
        except SchemaPublishError as e:
            logger.exception(e.error_message)
            self.error_notification_protocol.send_message(e, CONFIG.PUBLISH_SCHEMA_ERROR_TOPIC_ID)

    def _filter_github_files(self, files: list[str]) -> list[str]:  # noqa
        """
        Filter a list of file names to publish by the regex
        """
        pattern = re.compile(r"^schemas/[^/]+/[^/]+\.json$")
        return [f for f in files if pattern.match(f)]

    def publish_new_schemas(self, source: str, file_list: list[str]):
        """
        Take a list of file names and publish each one using a SchemaPublisher that is identified using publisher
        If any schema fails to publish, it will print an error message but continue processing the remaining files.

        :param source: string indicating the source of the schema files to be published
            Options are "GitHub", "bucket"
        :param file_list: List of file names to publish
        """

        source = source.lower()

        logger.info(f"Starting publishing new schemas, source: {source}")

        if source == "github":
            file_list = self._filter_github_files(file_list)
            for file_name in file_list:
                self._publish_single_file(file_name, publisher=self.repository_publisher)
        elif source == "bucket":
            for file_name in file_list:
                self._publish_single_file(file_name, publisher=self.bucket_publisher)
        else:
            raise SchemaSourceInvalidException(f"Invalid source: {source}")
