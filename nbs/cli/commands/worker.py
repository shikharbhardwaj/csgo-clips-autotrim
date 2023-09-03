import json
import logging
from pathlib import Path
import pathlib
import tempfile
import time
from typing import List
from typing_extensions import Annotated

import typer

from PIL import Image

from csgo_clips_autotrim.experiment_utils.config import DBConfig, StorageConfig
from csgo_clips_autotrim.autotrim import TimelineEvent
from cli.commands import segment, preprocess, clutch
from cli.database import Database
from cli.storage import S3BlobStorage
from cli.models import IngestEntry, ResultEntry
from webserver.models import TaskStatus

logger = logging.getLogger(__name__)

app = typer.Typer()

default_db_config = DBConfig.from_env()
default_storage_config = StorageConfig.from_env()

@app.callback(invoke_without_command=True)
def worker(source_dir: Annotated[Path,
                                typer.Option(
                                file_okay=False,
                                dir_okay=True,
                                writable=False,
                                readable=True,
                                resolve_path=True,
                                envvar='AUTOTRIM_SOURCE_DIR'
                                )],
          db_config_path: Annotated[Path,
                                typer.Option(
                                file_okay=False,
                                dir_okay=True,
                                writable=False,
                                readable=True,
                                resolve_path=True,
                                )] = None,
          storage_config_path: Annotated[Path,
                                typer.Option(
                                file_okay=False,
                                dir_okay=True,
                                writable=False,
                                readable=True,
                                resolve_path=True,
                                )] = None):
    if not source_dir.exists():
        logger.error('Source dir: %s does not exist.', source_dir.as_posix())
        raise ValueError()

    if db_config_path is None:
        db_config = default_db_config
    else:
        with open(db_config, 'r') as f:
            db_config = DBConfig.schema().load(f)

    if storage_config_path is None:
        storage_config = default_storage_config
    else:
        with open(storage_config_path, 'r') as f:
            storage_config = DBConfig.schema().load(f)
    
    db = Database(db_config)
    storage = S3BlobStorage(endpoint_url=storage_config.endpoint_url)

    # Get one ingest task.
    candidates = IngestEntry.search_ingest_entry(db, status=(TaskStatus.ACCEPTED,), limit=1)
    logger.info('Got %d candidates from db.', len(candidates))

    if not candidates:
        logger.info('No ingest entry remaining to work on.')
        return
    
    ingest_entry = candidates[0]
    ingest_entry.status = TaskStatus.RUNNING
    ingest_entry.save(db)
    logger.info('Working on ingest entry: %s', ingest_entry)

    try:
        work_dir = tempfile.mkdtemp(prefix='autotrim-')

        # with tempfile.TemporaryDirectory(prefix='autotrim-', ) as work_dir:
        if True:
            logger.info('Wok dir: %s', work_dir)
            video_path = source_dir / ingest_entry.path

            work_dir = pathlib.Path(work_dir)
            frame_dir = work_dir / 'frames'
            segmenation_results_dir = work_dir / 'segmentation-results'

            # Step 1. Get downsampled frames.
            try:
                tic = time.perf_counter()
                preprocess.downsample(video_path, output_dir=frame_dir)
                toc = time.perf_counter()
                logger.info('Finished preprocessing in %f seconds', toc - tic)
            except:
                logger.exception('Failed to get downsampled frames.')
                raise

            # Step 2. Elimination segmentation.
            try:
                tic = time.perf_counter()
                segment.elimination(frame_dir, output_dir=segmenation_results_dir)
                toc = time.perf_counter()
                logger.info('Finished segmentation elimination in %f seconds', toc - tic)
            except:
                logger.exception('Failed to get segmentation results.')
                raise
            
            # Step 3. Perform clutch detection.
            try:
                tic = time.perf_counter()
                clutch.detect(work_dir=work_dir)
                toc = time.perf_counter()
                logger.info('Finished clutch detection in %f seconds', toc - tic)
            except:
                logger.exception('Failed to perform clutch detection.')
                raise

            # Store a few result artifacts:
            # 1. Clutch detection result JSON (in DB)
            # 2. Timeline (in DB)
            # 3. Timeline frames (in blobstore)
            timeline_result_path = work_dir / 'timeline.json'
            timeline_result = json.loads(timeline_result_path.read_text())

            clutch_detection_result = None
            clutch_detection_result_path = work_dir / 'clutch_result.json'

            if clutch_detection_result_path.exists():
                clutch_detection_result = json.loads(clutch_detection_result_path.read_text())
            
            result_entry = ResultEntry(ingest_id=ingest_entry.ingest_id,
                                       timeline=timeline_result,
                                       clutch_detection_result=clutch_detection_result)
            result_entry.save(db)

            timeline_events: List[TimelineEvent] = [
                TimelineEvent.from_dict(x) for x in timeline_result['timeline']
            ]

            # Upload timeline frames to blob store.
            for event in timeline_events:
                frame_path = frame_dir / f'{event.frame_info.name}.png'
                storage.put(frame_path,
                            storage_config.bucket_prefix + f'/ingests/{ingest_entry.ingest_id}/timeline/{frame_path.name}')

        ingest_entry.status = TaskStatus.SUCCESS
        ingest_entry.save(db)
    except:
        logger.info('Storing task status to FAILED')
        ingest_entry.status = TaskStatus.FAILED
        ingest_entry.save(db)
