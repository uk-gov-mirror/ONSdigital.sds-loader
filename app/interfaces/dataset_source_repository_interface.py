from abc import ABC, abstractmethod

from app.models.dataset import RawDataset


class DatasetSourceRepositoryInterface(ABC):
    """
    This interface defines where datasets are originally stored
    before being moved to their storage location

    E.g. DatasetSource would be a bucket
    """

    @abstractmethod
    def get_oldest_filename(self) -> str | None:
        """
        Returns the filename of the oldest file in the source repository.

        :returns: The filename of the oldest file in the source repository, or none
        if there are no files in the source repository
        """
        ...

    @abstractmethod
    def get_raw_data(self, file_name: str) -> RawDataset | None:
        """
        Returns the raw content of a file in the source repository.

        :param file_name: The name of the file to return
        :returns: The raw content of a file in the source repository or None if not found
        :raises DatasetValidationException if the contents does not conform to RawDataset
        """
        ...

    @abstractmethod
    def delete_raw_data(self, file_name: str) -> None:
        """
        Deletes the raw content of a file in the source repository.

        :param file_name: The name of the file to delete
        """
        ...
