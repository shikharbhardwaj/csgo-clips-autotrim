import logging
from logging.config import dictConfig
from typing import List
import time
from functools import wraps
import math
from urllib.parse import urlparse
import os

from .constants import LOGGING_CONFIG


def split_batches(xs: List, batch_size: int):
    num_batches = int(math.ceil(len(xs) / batch_size))
    batches = [xs[batch_size * i: batch_size * (i + 1)] for i in range(num_batches)]
    return batches


def logged_timer(logger):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            tic = time.perf_counter()
            result = function(*args, **kwargs)
            toc = time.perf_counter()

            logger.info(f"Executed {function.__name__} in {toc - tic:0.4f} seconds")

            return result
        return wrapper
    return decorator


def getLogger():
    dictConfig(LOGGING_CONFIG)
    return logging.getLogger()
