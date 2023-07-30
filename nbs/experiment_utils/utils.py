from collections import namedtuple
import copy
import functools
import json
import logging
from logging import config as logging_config
import math
import os
import pathlib
import time
import tempfile

from typing import List, Optional

import pandas as pd

from .constants import *


def getLogger(name: str = 'default'):
    logging_config.dictConfig(LOGGING_CONFIG)
    return logging.getLogger(name)

logger = getLogger('utils')

def split_batches(xs: List, batch_size: int):
    num_batches = int(math.ceil(len(xs) / batch_size))
    batches = [xs[batch_size * i: batch_size * (i + 1)] for i in range(num_batches)]
    return batches


def logged_timer(logger):
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            tic = time.perf_counter()
            result = function(*args, **kwargs)
            toc = time.perf_counter()

            logger.info(f"Executed {function.__name__} in {toc - tic:0.4f} seconds")

            return result
        return wrapper
    return decorator


def get_sample_videos_paths():
    clips_dir = os.path.join(DATA_DIR, 'clips')
    return [os.path.join(clips_dir, name) for name in os.listdir(clips_dir)]


def get_data_path(suffix_path: List[str]):
    return os.path.join(DATA_DIR, *suffix_path)


def add_image_list_to_label_studio_coco_annotations(annotations_path: str, image_list_path: str, base_path: Optional[str]) -> str:
    """ Utility to fix bug in label studio annotation exports not including samples
    without any annotations.

    Args:
        annotations_path (str):
        image_list_path (str):
        base_path (Optional[str]): 
    
    Returns:
        str: Path to fixed annotations json file.
    """
    assert pathlib.Path(annotations_path).exists(), 'Annotations path does not exist'
    assert pathlib.Path(image_list_path).exists(), 'Annotations path does not exist'

    if base_path is None:
        base_path = ''

    with open(annotations_path, 'r') as f:
        annotations_data = json.load(f)

    with open(image_list_path, 'r') as f:
        image_names = [x.strip() for x in f.readlines() if x.strip()]

    image_paths = {base_path + x for x in image_names}
    existing_image_paths = {x['file_name'] for x in annotations_data['images']}

    image_width = annotations_data['images'][0]['width']
    image_height = annotations_data['images'][0]['height']

    assert image_width is not None, 'Could not find image width from existing annotation'
    assert image_height is not None, 'Could not find image height from existing annotation'

    cur_id = annotations_data['images'][-1]['id']

    fixed_annotations_data = copy.deepcopy(annotations_data)

    for path in image_paths - existing_image_paths:
        entry = {'width': image_width, 'height': image_height, 'id': cur_id, 'file_name': path}
        fixed_annotations_data['images'].append(entry)
        cur_id += 1
    
    with tempfile.NamedTemporaryFile(prefix='annotations', suffix='.json', delete=False) as f:
        json.dump(fixed_annotations_data, f)

Tick = namedtuple('Tick', ['ts', 'description'])

class TimeSplitTracker:
    """Simple class to track time splits for a sequence of events in a function.
    """

    def __init__(self):
        self._ticks = []

    def add(self, descriptiion: str):
        self._ticks.append(Tick(ts=time.perf_counter(), description=descriptiion))
    
    def show_summary(self):
        if len(self._ticks) <= 1:
            logging.warning('No ticks to summarize.')
            return

        df = pd.DataFrame(self._ticks)
        ts_diff = df['ts'].diff()
        summary_df = pd.concat([df['description'].iloc[1:], ts_diff], axis=1).dropna()

        print(summary_df)
