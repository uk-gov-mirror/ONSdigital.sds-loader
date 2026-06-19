from unittest import TestCase
import pytest
from sds_common.config.config import CONFIG
from sds_common.enums.buckets import Bucket
from sds_common.repositories.bucket_loader import BucketLoader
from sds_common.services.file_service import FileService
from sds_common.test_helpers.common_test_data import test_schema_subscriber_id_success
from sds_common.test_helpers.integration_helpers import (
    cleanup,
    pubsub_setup,
    inject_wait_time,
    poll_subscription,
    pubsub_purge_messages,
    pubsub_teardown,
)
from sds_common.test_helpers.pub_sub_helper import PubSubHelper

from app.routes import logger


class SchemaPublishGcsIntegrationTest(TestCase):
    @classmethod
    def setup_class(cls):
        cleanup()
        cls.bucket_service = FileService(Bucket.SCHEMA_PUBLISH_BUCKET, BucketLoader())
        cls.schema_queue_pubsub_helper = PubSubHelper(CONFIG.PUBLISH_SCHEMA_QUEUE_TOPIC_ID)
        cls.schema_success_pubsub_helper = PubSubHelper(CONFIG.PUBLISH_SCHEMA_SUCCESS_TOPIC_ID)
        pubsub_setup(cls.schema_success_pubsub_helper, test_schema_subscriber_id_success)
        inject_wait_time(10)  # Inject wait time to allow resources to complete setting up

    @classmethod
    def teardown_class(cls) -> None:
        cleanup()
        inject_wait_time(3)  # Inject wait time to allow all messages to be processed
        pubsub_purge_messages(cls.schema_success_pubsub_helper, test_schema_subscriber_id_success)
        pubsub_teardown(cls.schema_success_pubsub_helper, test_schema_subscriber_id_success)

    @pytest.mark.order(1)
    def test_publish_schema_to_gcs(self):
        """
        Test publishing a schema via GCS happy path.

        *We drop a valid schema file into the GCS schema publish bucket
        *We poll the schema_success_topic to check if the schema was published.
        *We assert that the schema was published successfully.

        """

        logger.info(f"Success topic: {CONFIG.PUBLISH_SCHEMA_SUCCESS_TOPIC_ID}")

        self.bucket_service.upload_file("integration_tests/test_data/test_schema_success.json")

        messages = poll_subscription(self.schema_success_pubsub_helper, test_schema_subscriber_id_success)

        logger.info(f"Received messages: {messages}")

        assert messages is not None
        for message in messages:
            assert "guid" in message
