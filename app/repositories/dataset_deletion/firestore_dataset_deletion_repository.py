from datetime import datetime, timezone

from typing import Protocol

from google.cloud import firestore

from app import get_logger
from app.enums.delete_status import DeleteStatus
from app.exceptions.dataset_deletion_mark_exception import DatasetDeletionMarkException
from app.interfaces.dataset_deletion_repository_interface import DatasetDeletionRepositoryInterface
from app.models.guid import Guid

logger = get_logger()


class FirestoreSettings(Protocol):
    project_id: str
    firestore_database: str


class FirestoreDatasetDeletionRepository(DatasetDeletionRepositoryInterface):
    """
    An implementation of a DatasetDeletionRepository that stores
    delete records in firestore
    """

    def __init__(
        self,
        settings: FirestoreSettings,
    ):
        self.settings = settings

        # Create a firestore client
        self.client = firestore.Client(project=self.settings.project_id, database=self.settings.firestore_database)

        # Initialize Firestore collections
        self.mark_deletion_collection = self.client.collection("marked_for_deletion")

        # Store a mapping of guids to firestore document id's in memory
        self.document_references = {}

    def mark_record_status(self, guid: Guid, status: DeleteStatus) -> None:
        # Look for the document reference in the cache
        doc_id = self.document_references.get(guid)

        # If for some reason the guid is not in the cache, query firestore for it
        if not doc_id:
            logger.warning(f"Marking record with guid that is not in repository cache: {guid}, looking in firestore...")

            results = self.mark_deletion_collection.where("dataset_guid", "==", guid).limit(1).stream()

            results_list = list(results)

            if len(results_list) > 0:
                doc_id = results_list[0].id
            else:
                raise DatasetDeletionMarkException(
                    f"Could not mark record with guid {guid} as a record with this guid could not be found"
                )

        try:
            # Update the status of this record in firestore
            document_reference = self.mark_deletion_collection.document(doc_id)
            document_reference.update({"status": status.value})

            # If the status is deleted, then mark a timestamp
            if status == DeleteStatus.DELETED:
                utc_dt = datetime.now(timezone.utc)  # UTC time
                dt = utc_dt.astimezone()  # local time
                timestamp = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                document_reference.update({"deleted_at": timestamp})
        except Exception as e:
            raise DatasetDeletionMarkException from e

    def get_dataset_to_delete(self) -> Guid | None:
        # First, try to fetch a PROCESSING dataset
        processing = self.mark_deletion_collection.where("status", "==", "processing").limit(1).stream()

        processing_list = list(processing)

        # If a result is found that is "Processing"

        if len(processing_list) > 0:
            # Pick the first record
            doc = processing_list[0]

            # Convert the data into a dictionary
            dataset = doc.to_dict()

            # Extract the fields we need
            guid = dataset.get("dataset_guid")
            doc_id = doc.id

            # Store in cache
            self.document_references[guid] = doc_id

            # Return the guid
            return guid

        # If no "Processing" results found, fetch a PENDING dataset
        pending = self.mark_deletion_collection.where("status", "==", "pending").limit(1).stream()

        pending_list = list(pending)

        if len(pending_list) > 0:
            doc = pending_list[0]

            # Convert the data into a dictionary
            dataset = doc.to_dict()

            # Extract the fields we need
            guid = dataset.get("dataset_guid")
            doc_id = doc.id

            # Store in cache
            self.document_references[guid] = doc_id

            # Return the guid
            return guid

        # Nothing found, then return None

        return None
