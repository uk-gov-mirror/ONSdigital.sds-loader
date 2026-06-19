from typing import Protocol

from sdx_base.services.pubsub import PubsubService

from app.interfaces.dataset_broadcast_interface import DatasetBroadcastInterface
from app.models.dataset import DatasetMetadata


class PubsubBroadcastSettings(Protocol):
    publish_dataset_topic_id: str


class PubsubBroadcaster(DatasetBroadcastInterface):
    """
    A broadcaster that will
    broadcast to pubsub
    """

    def __init__(
        self,
        settings: PubsubBroadcastSettings,
    ):
        self.settings = settings
        self.pubsub_client = PubsubService()

    def broadcast(self, dataset_metadata: DatasetMetadata) -> None:
        self.pubsub_client.publish_message(
            self.settings.publish_dataset_topic_id, dataset_metadata.model_dump_json(), {}
        )
