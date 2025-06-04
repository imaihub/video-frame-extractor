import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Union

from vfe.frame_extraction_strategy import FrameExtractionStrategy, AllFramesStrategy
from vfe.utils import VALID_VIDEO_EXTENSIONS, validate_output_path

logger = logging.getLogger(__name__)


class VideoFrameExtractor:
    """
    Core component responsible for orchestrating video frame extraction using a specific strategy.
    """
    VALID_EXTS = VALID_VIDEO_EXTENSIONS

    def __init__(self, video_path: Path, allow_any_extension: bool = False, output_dir: Optional[Path] = None,
                 fps: Optional[int] = None, start_time: Optional[float] = None, end_time: Optional[float] = None,
                 strategy: Optional[FrameExtractionStrategy] = None, reset_indices: bool = False,
                 verbose: bool = False) -> None:
        """Initialize the video frame extractor.

        :param video_path: Path to the input video.
        :param allow_any_extension: If True, allow any extension of the input video and let ffmpeg handle it.
        :param output_dir: Path to the output directory.
        :param fps: Frames per second to extract (not required for AllFramesStrategy ('all´)).
        :param start_time: Start time for extraction.
        :param end_time: End time for extraction.
        :param strategy: Frame extraction strategy (all, uniform, fixed_random).
        :param reset_indices: If True, frame numbering starts at 0 instead of using original frame indices.
        :param verbose: Whether to enable verbose logging.

        :raises FileNotFoundError: If the video_path does not exist.
        :raises ValueError: If the file extension is unsupported and allow_any_extension is False.
        :raises ValueError: If fps is provided and is non-positive.
        :raises ValueError: If start_time is negative.
        :raises ValueError: If end_time is negative or not greater than start_time.
        :raises TypeError: If strategy is not an instance of FrameExtractionStrategy.
        :raises OSError: If output_dir creation fails.
        """
        self.verbose = verbose
        if self.verbose:
            logger.setLevel(logging.INFO)

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video path '{video_path}' does not exist.")
        if not allow_any_extension and video_path.suffix.lower() not in self.VALID_EXTS:
            raise ValueError(f"Unsupported video format: {video_path.suffix}")
        self.video_path = video_path

        if output_dir is not None:
            self.output_dir = validate_output_path(output_dir, create_if_missing=True)

        if fps is not None and fps <= 0:
            raise ValueError(f"FPS must be positive; received: {fps}")
        self.fps = fps

        if start_time is not None and start_time < 0:
            raise ValueError(f"Start time cannot be negative; received: {start_time}")
        self.start_time = start_time

        if end_time is not None:
            if end_time < 0:
                raise ValueError(f"End time cannot be negative; received: {end_time}")
            if start_time is not None and end_time <= start_time:
                raise ValueError(f"End time ({end_time}) must be greater than start time ({start_time}).")
        self.end_time = end_time

        self.strategy = strategy or AllFramesStrategy(verbose=self.verbose)
        if not isinstance(self.strategy, FrameExtractionStrategy):
            raise TypeError(f"Strategy must be a FrameExtractionStrategy instance, got {type(self.strategy)}")

        self.reset_indices = reset_indices

    def extract_frames(self) -> None:
        """
        Extract frames using the assigned strategy.
        """
        if self.verbose:
            logger.info("Starting frame extraction...")

        metadata = self.get_metadata(fields=["duration", "avg_fps"])
        if metadata is None:
            raise ValueError("Could not retrieve video metadata.")

        self.strategy.extract_frames(
            video_path=self.video_path,
            output_dir=self.output_dir,
            fps=self.fps,
            start_time=self.start_time,
            end_time=self.end_time,
            metadata=metadata,
            reset_indices=self.reset_indices
        )

    def get_metadata(self, fields: Optional[List[str]] = None) -> Optional[Dict[str, Union[str, float, int]]]:
        """Retrieve and display video metadata using ffprobe.

        :param fields: Specific fields of metadata to retrieve.
        :return: Dictionary containing requested metadata fields.
        """
        try:
            command = [
                "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                "stream=width,height,codec_name,r_frame_rate,avg_frame_rate,duration,nb_frames,bit_rate",
                "-of", "json", self.video_path
            ]
            result = subprocess.check_output(command).decode()
            metadata = json.loads(result)
            stream = metadata.get("streams", [{}])[0]

            avg_fps = eval(stream.get("avg_frame_rate", "0/1"))
            bitrate_kbps = int(stream.get("bit_rate", 0)) // 1000

            video_info = {
                "codec": stream.get("codec_name", "Unknown"),
                "resolution": f"{stream.get('width', 'Unknown')}x{stream.get('height', 'Unknown')}",
                "avg_fps": avg_fps,
                "duration": float(stream.get("duration", 0)),
                "total_frames": int(stream.get("nb_frames", "0")),
                "bitrate": bitrate_kbps
            }

            if fields:
                return {key: video_info[key] for key in fields if key in video_info}
            return video_info

        except Exception as e:
            logger.error(f"Error retrieving metadata: {e}")
            return None
