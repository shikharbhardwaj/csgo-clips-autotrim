import dataclasses
import json
import logging
from pathlib import Path
from typing import Annotated
import tqdm

import mmcv
import typer

from csgo_clips_autotrim.experiment_utils.config import InferenceConfig
from csgo_clips_autotrim.ocr import TritonOCR
from csgo_clips_autotrim.segmentation import elimination as elimination_segmentation
from csgo_clips_autotrim.segmentation import postprocessing

log = logging.getLogger(__name__)

app = typer.Typer()

ELIMINATION_MODEL_RUN_ID = '254e228656e348078b8663502a68065a'
ELIMINATION_MODEL_NAME='csgo-elimination-segmentation-yolov8'
ELIMINATION_SCORE_THRESHOLD = 0.5
TRITON_URL = 'localhost:8000'

default_elimination_inference_config = InferenceConfig(
         mlflow_artifact_run_id=ELIMINATION_MODEL_RUN_ID,
         triton_model_name=ELIMINATION_MODEL_NAME,
         triton_url=TRITON_URL,
         score_threshold=ELIMINATION_SCORE_THRESHOLD)

WEAPON_MODEL_RUN_ID = 'ab4eddb8e281440c882d5d8771844c9c'
WEAPON_MODEL_NAME = 'csgo-elimination-weapon-segmentation-yolov8'
WEAPON_SCORE_THRESHOLD = 0.5

default_weapon_inference_config = InferenceConfig(
         mlflow_artifact_run_id=WEAPON_MODEL_RUN_ID,
         triton_model_name=WEAPON_MODEL_NAME,
         triton_url=TRITON_URL,
         score_threshold=WEAPON_SCORE_THRESHOLD)

OCR_MODEL_RUN_ID = '9a143aad0ca04da583484b3471248aed'
OCR_MODEL_NAME = 'paddleocr-en_PP-OCRv3-rec'
OCR_SCORE_THRESHOLD = 0.5

default_ocr_inference_config = InferenceConfig(
         mlflow_artifact_run_id=OCR_MODEL_RUN_ID,
         triton_model_name=OCR_MODEL_NAME,
         triton_url=TRITON_URL,
         score_threshold=OCR_SCORE_THRESHOLD)

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
                  elimination_inference_config_path: Annotated[Path,
                                     typer.Option(
                                        file_okay=False,
                                        dir_okay=True,
                                        writable=False,
                                        readable=True,
                                        resolve_path=True,
                                     )] = None,
                  weapon_inference_config_path: Annotated[Path,
                                     typer.Option(
                                        file_okay=False,
                                        dir_okay=True,
                                        writable=False,
                                        readable=True,
                                        resolve_path=True,
                                     )] = None,
                  ocr_inference_config_path: Annotated[Path,
                                     typer.Option(
                                        file_okay=False,
                                        dir_okay=True,
                                        writable=False,
                                        readable=True,
                                        resolve_path=True,
                                     )] = None,
                  ):
   """Extract the elimination information from the given frame.

   Args:
       image_dir_path (Path): Path to folder containig image to extract information from.
       output_dir (Path): Path to output directory, with output in JSON format. Defaults to './out'.
   """
   if not output_dir.exists():
      output_dir.mkdir(parents=True)

   if elimination_inference_config_path is None:
      elimination_inference_config = default_elimination_inference_config
   else:
      with open(elimination_inference_config_path, 'r') as f:
         elimination_inference_config = InferenceConfig.schema().load(f)

   if weapon_inference_config_path is None:
      weapon_inference_config = default_weapon_inference_config
   else:
      with open(weapon_inference_config_path, 'r') as f:
         weapon_inference_config = InferenceConfig.schema().load(f)

   if ocr_inference_config_path is None:
      ocr_inference_config = default_ocr_inference_config
   else:
      with open(ocr_inference_config_path, 'r') as f:
         ocr_inference_config = InferenceConfig.schema().load(f)
   
   ocr = TritonOCR(ocr_inference_config)

   images = image_dir_path.glob('*.png')

   for image_path in tqdm.tqdm(images):
      input_img = mmcv.imread(image_path)
      input_rgb = mmcv.imconvert(input_img, 'bgr', 'rgb')

      height, width, channels = input_rgb.shape
      mid_height, mid_width = height // 2, width // 2
      cropped_input = input_rgb[:mid_height, mid_width:, :]

      preprocess_result = elimination_segmentation.preprocess_image(cropped_input, elimination_inference_config.mlflow_artifact_run_id)
      segmentation_result = elimination_segmentation.segment_elimination_events(preprocess_result, image_path, elimination_inference_config)

      events_with_added_info = []

      for event in segmentation_result.elimination_events:
         weapon_segmentation_input = elimination_segmentation.get_weapon_segmentation_input(cropped_input, event)
         weapon_segmentation_input_prep = elimination_segmentation.preprocess_image(weapon_segmentation_input, weapon_inference_config.mlflow_artifact_run_id)
         weapon_segmentation_result = elimination_segmentation.segment_weapon(event, weapon_segmentation_input_prep, weapon_inference_config)
         player_recognition_result = elimination_segmentation.recognize_players(weapon_segmentation_result, cropped_input, ocr)

         events_with_added_info.append(player_recognition_result)
      
      segmentation_result = dataclasses.replace(segmentation_result, elimination_events=events_with_added_info)
      segmentation_result = postprocessing.remove_duplicate_events(segmentation_result)

      name_stem = image_path.stem
      json_path = output_dir / f'{name_stem}.json'

      data = {}
      # If the json already exists, append data to it.
      if json_path.exists():
         with open(json_path, 'r') as f:
            data = json.load(f)

         data['elimination_events'] = segmentation_result.to_dict()['elimination_events']
      else:
         data = segmentation_result.to_dict()

      with open(json_path, 'w') as f:
         json.dump(data, f, indent=4)
