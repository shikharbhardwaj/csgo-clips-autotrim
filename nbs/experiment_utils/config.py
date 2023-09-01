import dataclasses
import os
import dataclasses_json

@dataclasses_json.dataclass_json
@dataclasses.dataclass
class InferenceConfig:
    mlflow_artifact_run_id: str
    triton_model_name: str
    triton_url: str
    score_threshold: float


@dataclasses_json.dataclass_json
@dataclasses.dataclass
class DBConfig:
    name: str
    user: str
    password: str
    host: str
    port: str

    @classmethod
    def from_env(cls) -> 'DBConfig':
        return cls(
            name = os.getenv('DB_NAME', 'autotrim'),
            host = os.getenv('DB_HOST', 'localhost'),
            port = os.getenv('DB_PORT', '5432'),
            user = os.getenv('DB_USER', 'postgres'),
            password = os.getenv('DB_PASS', 'password')
        )

@dataclasses_json.dataclass_json
@dataclasses.dataclass
class StorageConfig:
    bucket_prefix: str
    endpoint_url: str

    @classmethod
    def from_env(cls) -> 'StorageConfig':
        return cls(
            bucket_prefix=os.getenv('AUTOTRIM_STORAGE_BUCKET_PREFIX', 's3://autotrim/dev'),
            endpoint_url=os.getenv('AUTOTRIM_STORAGE_ENDPOINT_URL', 'https://minio-api.tenzing.shkhr.ovh')
        )