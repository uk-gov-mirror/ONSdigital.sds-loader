import json
from typing import Protocol, Optional

from google.cloud.storage import Blob

from app.exceptions.dataset_validation_exception import DatasetValidationException
from app.interfaces.dataset_source_repository_interface import DatasetSourceRepositoryInterface
from app.models.dataset import RawDataset


class BucketReader(Protocol):
    def get_blobs(
        self, bucket_name: str, project_id: Optional[str] = None, directory: Optional[str] = None
    ) -> list[Blob]: ...

    def read(
        self, filename: str, bucket_name: str, sub_dir: Optional[str] = None, project_id: Optional[str] = None
    ) -> bytes: ...

    def delete(
        self, filename: str, bucket_name: str, sub_dir: Optional[str] = None, project_id: Optional[str] = None
    ) -> bool: ...


class BucketSettings(Protocol):
    dataset_bucket_name: str


class BucketDatasetSourceRepository(DatasetSourceRepositoryInterface):
    """
    This repository is an implementation of the DatasetSourceRepositoryInterface that
    uses GCP buckets
    """

    def __init__(self, bucket_reader: BucketReader, settings: BucketSettings) -> None:
        self._bucket_reader = bucket_reader
        self._settings = settings

    def get_oldest_filename(self) -> str | None:
        blobs = self._bucket_reader.get_blobs(self._settings.dataset_bucket_name)

        valid_blobs = (blob for blob in blobs if blob.updated is not None and blob.name is not None)

        oldest_blob = min(
            valid_blobs,
            key=lambda blob: (blob.updated, blob.name),
            default=None,
        )

        return oldest_blob.name if oldest_blob else None

    def get_raw_data(self, file_name: str) -> RawDataset | None:
        # Read the raw data from the bucket
        data_bytes = self._bucket_reader.read(file_name, bucket_name=self._settings.dataset_bucket_name)

        # If not found, return None
        if data_bytes is None:
            return None

        # Convert to JSON
        json_content = json.loads(data_bytes.decode("utf-8"))

        # Create the RawDataset and return
        try:
            return RawDataset.model_validate(json_content)
        except Exception as e:
            raise DatasetValidationException(f"Failed to validate dataset from file {file_name}: {e}")

    def delete_raw_data(self, file_name: str) -> None:
        # Delete from Bucket
        self._bucket_reader.delete(file_name, bucket_name=self._settings.dataset_bucket_name)
