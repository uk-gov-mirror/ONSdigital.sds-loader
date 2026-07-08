from typing import Protocol

from google.cloud import firestore
from google.cloud.firestore_v1.bulk_writer import BulkWriterOptions

from app import get_logger
from app.interfaces.dataset_storage_repository_interface import DatasetStorageRepositoryInterface
from app.models.dataset import DatasetMetadataWithoutId, UnitDataset, DatasetMetadata
from app.models.guid import Guid

logger = get_logger()


class FirestoreSettings(Protocol):
    project_id: str
    firestore_database: str


class FirestoreDatasetStorageRepository(DatasetStorageRepositoryInterface):
    """
    This repository is an implementation of DatasetStorageRepositoryInterface
    that uses firestore
    """

    def __init__(self, settings: FirestoreSettings):
        self.settings = settings

        # Create a firestore client
        self.client = firestore.Client(
            project=self.settings.project_id,
            database=self.settings.firestore_database,
        )

        logger.info(
            f"Connected to Firestore with project_id: {settings.project_id} and database: {settings.firestore_database}"
        )

        # Initialize Firestore collections
        self.dataset_collection = self.client.collection("datasets")

    def get_latest_dataset_metadata(self, survey_id: str, period_id: str) -> DatasetMetadataWithoutId | None:
        latest_dataset = (
            self.dataset_collection.where("survey_id", "==", survey_id)
            .where("period_id", "==", period_id)
            .order_by("sds_dataset_version", direction=firestore.Query.DESCENDING)
            .limit(1)
            .stream()
        )

        datasets = list(latest_dataset)

        # If no results then return None
        if len(datasets) == 0:
            return None

        # Parse into Pydantic Model
        return DatasetMetadataWithoutId.model_validate(datasets[0].to_dict())

    def _get_dataset_metadata(self, survey_id: str, period_id: str, version: int) -> DatasetMetadata | None:
        latest_dataset = (
            self.dataset_collection.where("survey_id", "==", survey_id)
            .where("period_id", "==", period_id)
            .where("sds_dataset_version", "==", version)
            .limit(1)
            .stream()
        )

        datasets = list(latest_dataset)

        # If no results then return None
        if len(datasets) == 0:
            return None

        return DatasetMetadata.model_validate(datasets[0].to_dict())

    def store_dataset(
        self,
        dataset_id: Guid,
        dataset_metadata: DatasetMetadataWithoutId,
        unit_data_collection_with_metadata: list[UnitDataset],
        unit_data_identifiers: list[str],
    ):
        logger.info("Writing to Firestore in BATCH mode")
        self._store_dataset_with_bulk_writer(
            dataset_id=dataset_id,
            dataset_metadata=dataset_metadata,
            unit_data_collection_with_metadata=unit_data_collection_with_metadata,
            unit_data_identifiers=unit_data_identifiers,
        )

    def _store_dataset_with_bulk_writer(
        self,
        dataset_id: Guid,
        dataset_metadata: DatasetMetadataWithoutId,
        unit_data_collection_with_metadata: list[UnitDataset],
        unit_data_identifiers: list[str],
    ):
        new_dataset_document = self.dataset_collection.document(dataset_id)
        units_collection = new_dataset_document.collection("units")

        bulk_writer = self.client.bulk_writer(options=BulkWriterOptions(max_ops_per_second=2500))

        try:
            # Include metadata in bulk
            bulk_writer.set(
                new_dataset_document,
                dataset_metadata.model_dump(),
                merge=False,
            )

            for unit, unit_identifier in zip(
                unit_data_collection_with_metadata,
                unit_data_identifiers,
            ):
                bulk_writer.set(
                    units_collection.document(unit_identifier),
                    unit.model_dump(),
                    merge=False,
                )

            bulk_writer.flush()

        finally:
            bulk_writer.close()

    def delete_dataset_version(self, survey_id: str, period_id: str, version: int):
        dataset_metadata = self._get_dataset_metadata(survey_id, period_id, version)

        if not dataset_metadata:
            logger.warning("Attempting delete dataset previous version, but it could not be found.")
            return

        # Delete the dataset now we have a guid for it
        self.delete_dataset_by_guid(dataset_metadata.dataset_id)

    def delete_dataset_by_guid(self, guid: Guid):
        # Get all the collections for this dataset
        collections = self.dataset_collection.document(guid).collections()

        # Delete each collection
        for collection in collections:
            self.client.recursive_delete(collection)

        # Delete the dataset itself
        self.dataset_collection.document(guid).delete()
