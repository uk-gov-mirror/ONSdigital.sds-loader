import json


from app import get_logger

logger = get_logger()


def get_file_path_from_bucket_notification(raw_data) -> str:
    """
    Extract the file name from the bucket notification message
    """
    raw_dict = json.loads(raw_data)
    logger.debug("Bucket notification message: ", raw_dict)
    return raw_dict["name"]


def get_file_paths_from_github_notification(raw_data) -> list[str]:
    """
    Extract the file names from the GitHub notification message
    """
    return raw_data.split("\n")
