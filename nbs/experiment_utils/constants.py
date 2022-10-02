import os
import logging
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent.absolute()
DATA_DIR = BASE_DIR / 'data'
CONFIG_DIR = BASE_DIR / 'config'


LOGGING_CONFIG = {'version': 1, 'formatters': {
    'f': {'format': '[%(levelname)-4s] %(asctime)s %(name)-12s: %(message)s'}
}, 'handlers': {
    'h': {'class': 'logging.StreamHandler',
          'formatter': 'f',
          'level': logging.INFO}
}, 'root': {
    'handlers': ['h'],
    'level': logging.INFO,
}}
