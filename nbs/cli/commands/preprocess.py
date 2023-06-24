import logging
from pathlib import Path
from typing_extensions import Annotated

import typer
from PIL import Image

from csgo_clips_autotrim.feature_extraction import get_downsampled_frames, DownsampleConfig

log = logging.getLogger(__name__)

app = typer.Typer()

@app.command()
def downsample(video_path: Annotated[Path,
                                     typer.Option(
                                        exists=True,
                                        file_okay=True,
                                        dir_okay=False,
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
                                     downsample_config: str = 'downsample_1280x720_60_RGB'):
    """Downsample the given video into individual frames according to the
    supplied downsample config.

    Args:
        video_path (Annotated[Path, typer.Option, optional): Path to video file to downsample. Defaults to True, file_okay=True, dir_okay=False, writable=False, readable=True, resolve_path=True, )].
        output_dir (Annotated[Path, typer.Option, optional): Path to output directory. Defaults to False, dir_okay=True, writable=False, readable=True, resolve_path=True, )]='./out'.
        downsample_config (str, optional): Downsample config represented by a string. Defaults to 'downsample_1280x720_60_RGB'.
    """
    downsample_config = DownsampleConfig.from_str(downsample_config)
    log.info('Downsampling config: %s', downsample_config)
    name_stem = video_path.stem
    frames = get_downsampled_frames(video_path.absolute().as_posix(), downsample_config)

    for idx, frame in enumerate(frames):
        name = f'{name_stem}_{idx:05}.png'
        img = Image.fromarray(frame)
        img.save(output_dir / name)
