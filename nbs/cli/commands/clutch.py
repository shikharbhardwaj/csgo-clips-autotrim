import json
import logging
import os
from pathlib import Path
from typing import Annotated

import typer

from csgo_clips_autotrim.experiment_utils.config import InferenceConfig
from csgo_clips_autotrim.autotrim import detect_clutch, get_timeline

log = logging.getLogger(__name__)

app = typer.Typer()

GAME_STATE_MODEL_RUN_ID = '2fe893e46e554b1e8b1ae44176677fb3'
GAME_STATE_MODEL_NAME = 'csgo-game-state-segmentation-yolov8'
GAME_STATE_SCORE_THRESHOLD = 0.5
TRITON_URL = os.getenv('TRITON_URL', 'localhost:8000')

default_game_state_inference_config = InferenceConfig(
    mlflow_artifact_run_id=GAME_STATE_MODEL_RUN_ID,
    triton_model_name=GAME_STATE_MODEL_NAME,
    triton_url=TRITON_URL,
    score_threshold=GAME_STATE_SCORE_THRESHOLD)

@app.command()
def detect(work_dir: Annotated[Path,
                                typer.Option(
                                file_okay=False,
                                dir_okay=True,
                                writable=False,
                                readable=True,
                                resolve_path=True,
                                )] = './out',
            game_state_inference_config_path: Annotated[Path,
                                typer.Option(
                                file_okay=False,
                                dir_okay=True,
                                writable=False,
                                readable=True,
                                resolve_path=True,
                                )] = None):
    """Detect clutch from the video with data in the given working directory.
    The working directory is the path where the output from previous steps
    (preprocessing and segmentation) is stored.

    Args:
        work_dir (Annotated[Path, typer.Option, optional): Defaults to False, dir_okay=True, writable=False, readable=True, resolve_path=True, )]='./out'.
        game_state_inference_config_path (Annotated[Path, typer.Option, optional): Defaults to False, dir_okay=True, writable=False, readable=True, resolve_path=True, )]=None.
    """
    if game_state_inference_config_path is None:
        game_state_inference_config = default_game_state_inference_config
    else:
        with open(game_state_inference_config_path, 'r') as f:
            game_state_inference_config = InferenceConfig.schema().load(f)
    
    log.info('Getting timeline from work dir: %s', work_dir)
    timeline = get_timeline(work_dir / 'segmentation-results')

    for event in timeline:
        log.info('Got timeline event in frame idx %d: %s', event.frame_info.idx, event.event)

    with open(work_dir / 'timeline.json', 'w') as f:
        json.dump({'timeline': [x.to_dict() for x in timeline]}, f, indent=4)
    
    log.info('Got %d events in timeline', len(timeline))
    log.info('Running clutch detection')
    result = detect_clutch(timeline, work_dir / 'frames', game_state_inference_config)

    if not result:
        log.info('No clutch detected.')
    else:
        log.info('Detected a clutch with %d eliminations, by %s', result.num_eliminations, result.player)
        with open(work_dir / 'clutch_result.json', 'w') as f:
            json.dump(result.to_dict(), f, indent=4)

