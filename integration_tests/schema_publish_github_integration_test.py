from unittest import TestCase

import pytest
from sds_common.config.config import CONFIG
from sds_common.test_helpers.integration_helpers import (
    cleanup,
    inject_wait_time,
    poll_subscription,
    pubsub_purge_messages,
    pubsub_setup,
    pubsub_teardown,
)
from sds_common.test_helpers.pub_sub_helper import PubSubHelper
from sds_common.test_helpers.common_test_data import (
    test_schema_subscriber_id_success,
    test_schema_subscriber_id_fail,
)

from integration_tests.test_data.test_filepaths import (
    test_schema_success_filepath,
    test_schema_fetch_error_filepath,
    test_schema_json_decode_error_filepath,
    test_schema_version_error_filepath,
    test_schema_survey_id_error_filepath,
    test_schema_version_mismatch_filepath,
)


class SchemaPublishIntegrationTest(TestCase):
    @classmethod
    def setup_class(cls):
        cleanup()
        cls.schema_queue_pubsub_helper = PubSubHelper(CONFIG.PUBLISH_SCHEMA_QUEUE_TOPIC_ID)
        cls.schema_success_pubsub_helper = PubSubHelper(CONFIG.PUBLISH_SCHEMA_SUCCESS_TOPIC_ID)
        cls.schema_error_pubsub_helper = PubSubHelper(CONFIG.PUBLISH_SCHEMA_ERROR_TOPIC_ID)
        pubsub_setup(cls.schema_success_pubsub_helper, test_schema_subscriber_id_success)
        pubsub_setup(cls.schema_error_pubsub_helper, test_schema_subscriber_id_fail)
        inject_wait_time(10)  # Inject wait time to allow resources properly set up

    @classmethod
    def teardown_class(cls) -> None:
        cleanup()
        inject_wait_time(3)  # Inject wait time to allow all message to be processed
        pubsub_purge_messages(cls.schema_success_pubsub_helper, test_schema_subscriber_id_success)
        pubsub_teardown(cls.schema_success_pubsub_helper, test_schema_subscriber_id_success)

    @pytest.mark.order(1)
    def test_publish_schema_success(self):
        """
        Test the publish-schema Cloud Function happy path.

        * We drop a message containing the filepath to a valid schema onto the queue.
        * We poll the schema_success_topic to check if the schema was published.
        * We assert that the schema was published successfully.
        """

        self.schema_queue_pubsub_helper.publish_message("schemas/test_schemas/test_schema_success.json")

        messages = poll_subscription(self.schema_success_pubsub_helper, test_schema_subscriber_id_success)

        assert messages is not None
        for message in messages:
            assert "guid" in message

    @pytest.mark.order(2)
    def test_publish_schema_schema_duplication_error(self):
        """
        Test the publish-schema Cloud Function returns SchemaDuplicationError.

        * We drop a message containing the filepath to a valid schema onto the queue.
        * We poll the schema_fail topic to check the error message.
        * We assert that the error is SchemaDuplicationError.
        """
        self.schema_queue_pubsub_helper.publish_message(test_schema_success_filepath)

        messages = poll_subscription(self.schema_error_pubsub_helper, test_schema_subscriber_id_fail)

        assert messages is not None
        for message in messages:
            assert "error_type" in message
            assert message["error_type"] == "SchemaDuplicationError"

    @pytest.mark.order(3)
    def test_publish_schema_schema_version_mismatch_error(self):
        """
        Test the publish-schema Cloud Function returns SchemaVersionMismatchError.

        * We drop a message containing the filepath to a schema with a mismatched version onto the queue.
        * We poll the schema_fail topic to check the error message.
        * We assert that the error is SchemaVersionMismatchError.
        """
        self.schema_queue_pubsub_helper.publish_message(test_schema_version_mismatch_filepath)

        messages = poll_subscription(self.schema_error_pubsub_helper, test_schema_subscriber_id_fail)

        assert messages is not None
        for message in messages:
            assert "error_type" in message
            assert message["error_type"] == "SchemaVersionMismatchError"

    @pytest.mark.order(4)
    def test_publish_schema_survey_id_error(self):
        """
        Test the publish-schema Cloud Function returns SurveyIDError.

        * We drop a message containing the filepath to a schema with a missing survey_id onto the queue.
        * We poll the schema_fail topic to check the error message.
        * We assert that the error is SurveyIDError.
        """
        self.schema_queue_pubsub_helper.publish_message(test_schema_survey_id_error_filepath)

        messages = poll_subscription(self.schema_error_pubsub_helper, test_schema_subscriber_id_fail)

        assert messages is not None
        for message in messages:
            assert "error_type" in message
            assert message["error_type"] == "SurveyIdError"

    @pytest.mark.order(5)
    def test_schema_version_error(self):
        """
        Test the publish-schema Cloud Function returns SchemaVersionError.

        * We drop a message containing the filepath to a schema with a missing schema_version onto the queue.
        * We poll the schema_fail topic to check the error message.
        * We assert that the error is SchemaVersionError.
        """
        self.schema_queue_pubsub_helper.publish_message(test_schema_version_error_filepath)

        messages = poll_subscription(self.schema_error_pubsub_helper, test_schema_subscriber_id_fail)

        assert messages is not None
        for message in messages:
            assert "error_type" in message
            assert message["error_type"] == "SchemaVersionError"

    @pytest.mark.order(6)
    def test_schema_json_decode_error(self):
        """
        Test the publish-schema Cloud Function returns SchemaJSONDecodeError.

        * We drop a message containing a filepath with invalid JSON onto the queue.
        * We poll the schema_fail topic to check the error message.
        * We assert that the error is SchemaJSONDecodeError.
        """
        self.schema_queue_pubsub_helper.publish_message(test_schema_json_decode_error_filepath)

        messages = poll_subscription(self.schema_error_pubsub_helper, test_schema_subscriber_id_fail)

        assert messages is not None
        for message in messages:
            assert "error_type" in message
            assert message["error_type"] == "SchemaJSONDecodeError"

    @pytest.mark.order(7)
    def test_schema_fetch_error(self):
        """
        Test the publish-schema Cloud Function returns SchemaFetchError.

        * We drop a message containing a fake filepath onto the queue.
        * We poll the schema_fail topic to check the error message.
        * We assert that the error is SchemaFetchError.
        """
        self.schema_queue_pubsub_helper.publish_message(test_schema_fetch_error_filepath)

        messages = poll_subscription(self.schema_error_pubsub_helper, test_schema_subscriber_id_fail)

        assert messages is not None
        for message in messages:
            assert "error_type" in message
            assert message["error_type"] == "SchemaFetchError"
