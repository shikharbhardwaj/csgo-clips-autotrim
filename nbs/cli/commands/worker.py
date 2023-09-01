import logging
from pathlib import Path
import pathlib
import tempfile
import time
from typing_extensions import Annotated

import typer

from PIL import Image

from csgo_clips_autotrim.experiment_utils.config import DBConfig, StorageConfig
from cli.commands import segment, preprocess, clutch
from cli.database import Database
from cli.storage import S3BlobStorage
from cli.models import IngestEntry
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
                                )] = None,
          downsample_config: str = 'downsample_1280x720_60_RGB'):
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
    
    ingest_entry = candidates[0]
    ingest_entry.try_progress_status()
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
                return

            # Step 2. Elimination segmentation.
            try:
                tic = time.perf_counter()
                segment.elimination(frame_dir, output_dir=segmenation_results_dir)
                toc = time.perf_counter()
                logger.info('Finished segmentation elimination in %f seconds', toc - tic)
            except:
                logger.exception('Failed to get segmentation results.')
                return
            
            # Step 3. Perform clutch detection.
            try:
                tic = time.perf_counter()
                clutch.detect(work_dir=work_dir)
                toc = time.perf_counter()
                logger.info('Finished clutch detection in %f seconds', toc - tic)
            except:
                logger.exception('Failed to perform clutch detection.')
                return

            # TODO: store a few result artifacts:
            # 1. Clutch detection result JSON (in DB)
            # 2. Timeline JSON (in DB)
            # 3. Timeline frames (in blob storage)
    except:
        logger.info('Storing task status to FAILED')
        ingest_entry.status = TaskStatus.FAILED
        ingest_entry.save(db)
