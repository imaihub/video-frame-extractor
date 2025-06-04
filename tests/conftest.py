import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def ensure_sample_video() -> None:
    """
    Ensure that tests/data/sample.mp4 exists before tests run.
    Generates a 1-second black video using ffmpeg if it doesn't exist.

    :return: None
    """
    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "FFmpeg is not installed or not in your PATH. "
            "Install it via `sudo apt install ffmpeg` or see https://ffmpeg.org/download.html"
        )

    video_path = Path("tests/data/sample.mp4")
    video_path.parent.mkdir(parents=True, exist_ok=True)

    if not video_path.exists():
        print("Generating sample.mp4 for tests...")
        subprocess.run([
            "ffmpeg",
            "-f", "lavfi",
            "-i", "color=c=black:s=320x240:d=1",
            "-pix_fmt", "yuv420p",
            str(video_path)
        ], check=True)
