import collections
import datetime
import hashlib
import logging
import os
from pathlib import Path

from typing import Annotated

from joblib import Parallel, delayed
import tqdm
import typer

from csgo_clips_autotrim.experiment_utils.config import DBConfig
from cli.database import Database
from cli.models import IngestEntry

app = typer.Typer()
logger = logging.getLogger(__name__)

default_db_config = DBConfig.from_env()

def calculate_file_hash(file_path: os.PathLike, chunk_size: int=8192) -> str:
    """Calculate the file hash for comparing file identity.

    Args:
        file_path (os.PathLike):
        chunk_size (int, optional): Defaults to 8192.

    Returns:
        str: File hash.
    """
    hash_obj = hashlib.new('sha256')
    with open(file_path, "rb") as file:
        while chunk := file.read(chunk_size):
            hash_obj.update(chunk)

    digest = hash_obj.hexdigest()
    return digest[:32]

@app.callback(invoke_without_command=True)
def ingest(source_dir: Annotated[Path,
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
                                )] = None):
    """Ingest all videos in given path into the DB.

    Args:
        source_dir (Annotated[Path, typer.Option, optional): Defaults to False, dir_okay=True, writable=False, readable=True, resolve_path=True, )].
        db_config_path (Annotated[Path, typer.Option, optional): Defaults to False, dir_okay=True, writable=False, readable=True, resolve_path=True, )]=None.
    """
    if db_config_path is None:
        db_config = default_db_config
    else:
        with open(db_config_path, 'r') as f:
            db_config = DBConfig.schema().load(f)

    db = Database(db_config)
    # Find all .mp4 files.
    video_files = list(source_dir.rglob('????-??/*.mp4'))

    logger.info('Discovered %d videos in source dir', len(video_files))

    video_files_by_month = collections.defaultdict(list)

    for video in video_files:
        video_files_by_month[video.parent.name].append(video)

    sorted_months = sorted(video_files_by_month.keys())
    # Find the closest month which is not ingested.
    closest_month = None

    for month in sorted_months:
        month_path = source_dir / month
        metadata_path = month_path / 'meta'
        metadata_path.mkdir(parents=True, exist_ok=True)

        candidate_videos = [(path, os.path.getmtime(path)) for path in video_files_by_month[month]]
        if not candidate_videos:
            continue

        last_video: Path = max(candidate_videos, key=lambda x: x[1])[0]

        logger.info('Finding hash of the last video: %s', last_video)
        hash_file_path = metadata_path / f'{last_video.stem}.hash'

        if hash_file_path.exists():
            file_hash = hash_file_path.read_text().rstrip()
        else:
            file_hash = calculate_file_hash(last_video)
            hash_file_path.write_text(file_hash)

        ingest_entry = IngestEntry.search_ingest_entry(db, ingest_id=file_hash)

        if not ingest_entry:
            logger.info('Did not find the last video for month: %s, starting sync from this month', month)
            closest_month = month
            break
        else:
            logger.info('Found entry for last video for month %s, skipping', month)
    
    if not closest_month:
        logger.info('Up to date')
        return
    
    start_idx = sorted_months.index(closest_month)

    def ingest_video(video: os.PathLike):
        metadata_path = video.parent / 'meta'
        metadata_path.mkdir(parents=True, exist_ok=True)
        hash_file_path = metadata_path / f'{video.stem}.hash'

        if hash_file_path.exists():
            file_hash = hash_file_path.read_text().rstrip()
        else:
            file_hash = calculate_file_hash(video)
            hash_file_path.write_text(file_hash)

        relative_path = video.relative_to(source_dir).as_posix()

        local_db = Database(db_config)
        ingest_entry = IngestEntry(ingest_id=file_hash, path=relative_path, ingested_at_utc=datetime.datetime.utcnow())
        ingest_entry.save(local_db)

    for month in sorted_months[start_idx:]:
        logger.info('Ingesting videos for: %s', month)

        Parallel(n_jobs=4)(delayed(ingest_video)(path) for path in tqdm.tqdm(video_files_by_month[month], desc='Processing'))