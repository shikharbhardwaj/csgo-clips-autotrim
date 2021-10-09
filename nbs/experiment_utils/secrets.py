from dataclasses import dataclass, fields
import json
import logging
from logging.config import dictConfig
import os

from dataclasses_json import dataclass_json

from .constants import LOGGING_CONFIG, BASE_DIR

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


@dataclass_json
@dataclass
class Secrets:
    AZURE_BLOBSTORE_CONTAINER_URL: str

    @classmethod
    def try_load_from_secrets_file(cls) -> 'Secrets':
        default_location = os.path.abspath(os.path.join(BASE_DIR, '.local', 'secrets.json'))
        
        secrets_file_location = os.getenv('GLOBAL_SECRETS_FILE', default_location)

        if not os.path.exists(secrets_file_location):
            raise FileNotFoundError(f"Could not find secrets file at: {secrets_file_location}. Set env variable GLOBAL_SECRETS_FILE to the path to secrets.json.")
        
        try:
            with open(secrets_file_location, 'r') as f:
                return cls.from_json(f.read())
        except FileNotFoundError:
            raise ValueError(f"Could not find secrets file at: {secrets_file_location}.")
    
    @classmethod
    def try_load_from_env_vars(cls) -> 'Secrets':
        env_var_names = { field.name for field in fields(cls) }

        return cls.from_dict({k: v for k, v in os.environ.items() if k in env_var_names})

    
    @classmethod
    def load(cls) -> 'Secrets':
        secret_loaders = [Secrets.try_load_from_secrets_file, Secrets.try_load_from_env_vars]
        
        for loader in secret_loaders:
            try:
                return loader()
            except Exception:
                logger.warn("Failed to load secrets from loader: %s", loader.__name__)
                
        raise RuntimeError("Could not load secrets.")

