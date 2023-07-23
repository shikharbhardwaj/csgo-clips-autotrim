import json
import logging
from pathlib import Path
from typing import Annotated
import tqdm

import typer

from csgo_clips_autotrim.segmentation.elimination import segment_elimination_events, InferenceConfig

log = logging.getLogger(__name__)

app = typer.Typer()

SAMPLE_MODEL_RUN_ID = '254e228656e348078b8663502a68065a'
TRITON_URL = 'localhost:8000'
SCORE_THRESHOLD = 0.5
TRITON_MODEL_NAME='csgo-elimination-segmentation-yolov8'

@app.command()
def elimination(image_dir_path: Annotated[Path,
                                     typer.Option(
                                        exists=True,
                                        file_okay=False,
                                        dir_okay=True,
                                        writable=False,
                                        readable=True,
                                        # resolve_path=True,
                                     )],
                 output_dir: Annotated[Path,
                                     typer.Option(
                                        file_okay=False,
                                        dir_okay=True,
                                        writable=False,
                                        readable=True,
                                        resolve_path=True,
                                     )] = './out',
                  inference_config_path: Annotated[Path,
                                     typer.Option(
                                        file_okay=False,
                                        dir_okay=True,
                                        writable=False,
                                        readable=True,
                                        resolve_path=True,
                                     )] = None):
   """Extract the elimination information from the given frame.

   Args:
       image_dir_path (Path): Path to folder containig image to extract information from.
       output_dir (Path): Path to output directory, with output in JSON format. Defaults to './out'.
   """
   if inference_config_path is None:
      inference_config = InferenceConfig(
         mlflow_artifact_run_id=SAMPLE_MODEL_RUN_ID,
         triton_model_name=TRITON_MODEL_NAME,
         triton_url=TRITON_URL,
         score_threshold=SCORE_THRESHOLD)
   else:
      with open(inference_config_path, 'r') as f:
         inference_config = InferenceConfig.schema().load(f)

   images = image_dir_path.glob('*.png')

   for image_path in tqdm.tqdm(images):
      events = segment_elimination_events(image_path=image_path, inference_config=inference_config)

      name_stem = image_path.stem
      json_path = output_dir / f'{name_stem}.json'

      data = {}
      # If the json already exists, append data to it.
      if json_path.exists():
         with open(json_path, 'r') as f:
            data = json.load(f)

         data['elimination_events'] = events.to_dict()['elimination_events']
      else:
         data = events.to_dict()

      with open(json_path, 'w') as f:
         json.dump(data, f, indent=4)
