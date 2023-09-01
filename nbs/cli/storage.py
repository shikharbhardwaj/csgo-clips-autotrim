import abc
import pathlib
import pathlib
from typing import Optional
import urllib.parse

import boto3

class BlobStorage(abc.ABC):
    def __init__(self, *args, **kwargs):
        ...
    
    def get(self, blob_uri: str, local_path: pathlib.Path):
        ...

    def put(self, local_path: pathlib.Path, blob_uri: str):
        ...


class S3BlobStorage(BlobStorage):
    def __init__(self, endpoint_url: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._s3 = boto3.client('s3', endpoint_url=endpoint_url)

    def get(self, blob_uri: str, local_path: pathlib.Path):
        parsed_uri = urllib.parse.urlparse(blob_uri)
        bucket_name = parsed_uri.netloc
        key = parsed_uri.path[1:]  # Remove leading '/'
        self._s3.download_file(bucket_name, key, str(local_path))

    def put(self, local_path: pathlib.Path, blob_uri: str):
        parsed_uri = urllib.parse.urlparse(blob_uri)
        bucket_name = parsed_uri.netloc
        key = parsed_uri.path[1:]  # Remove leading '/'
        self._s3.upload_file(str(local_path), bucket_name, key)
