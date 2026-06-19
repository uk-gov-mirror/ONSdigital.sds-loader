from app.util.file_getters import get_file_path_from_bucket_notification


class TestFilePathFromBucketNotification:
    def test_get_file_path_from_bucket_notification(self):
        message_body = """
        {
          "kind": "storage#object",
          "id": "ons-bob-bob-europe-west2-schema-publish/test_schema_success.json/1779969476194898",
          "selfLink": "https://www.googleapis.com/storage/v1/b/ons-bob-europe-west2-schema-publish/o/test_schema_success.json",
          "name": "test_schema_success.json",
          "bucket": "ons-bob-europe-west2-schema-publish",
          "generation": "1779969476194898",
          "metageneration": "1",
          "contentType": "application/json",
          "timeCreated": "2026-05-28T11:57:56.213Z",
          "updated": "2026-05-28T11:57:56.213Z",
          "storageClass": "STANDARD",
          "timeStorageClassUpdated": "2026-05-28T11:57:56.213Z",
          "size": "2740",
          "md5Hash": "jebWNEPU2gTDk5zIxDB7xg==",
          "mediaLink": "https://storage.googleapis.com/download/storage/v1/b/ons-bob-europe-west2-schema-publish/o/test_schema_success.json?generation=1779969476194898&alt=media",
          "crc32c": "k2Ihmw==",
          "etag": "CNLk24L325QDEAE="
        }
        """

        expected_name = "test_schema_success.json"
        assert get_file_path_from_bucket_notification(message_body) == expected_name
