import logging
import os
import random
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Union, Tuple

logger = logging.getLogger(__name__)


class FrameExtractionStrategy(ABC):
    """
    Abstract Base class for frame extraction strategies.

    Subclasses must define `STRATEGY_NAME` and implement `extract_frames()`.
    """
    STRATEGY_NAME: str

    def __init__(self, verbose: bool = False) -> None:
        """
        Initialize the frame extraction strategy.

        :param verbose: Enable verbose logging output.
        """
        self.verbose = verbose

    @abstractmethod
    def extract_frames(self, video_path: Path, output_dir: Path, fps: Optional[int] = None,
                       start_time: Optional[float] = None, end_time: Optional[float] = None,
                       metadata: Optional[Dict[str, Union[str, float, int]]] = None, reset_indices: bool = False) \
            -> None:
        """
        Extract frames based on the implemented strategy.

        :param video_path: Path to the video file.
        :param output_dir: Directory to save the extracted frames.
        :param fps: Frames per second or total number of frames (strategy-dependent).
        :param start_time: Extraction start time (seconds).
        :param end_time: Extraction end time (seconds).
        :param metadata: Video metadata dictionary.
        :param reset_indices: Reset frame indices to start from zero.
        """
        pass

    def common_frame_extraction_logic(self, video_path: Path, filter_args: List[str], output_dir: Path,
                                      start_time: Optional[float] = None, end_time: Optional[float] = None,
                                      reset_indices: bool = False) -> None:
        """
        Execute common frame extraction logic with ffmpeg.

        :param video_path: Path to the video file.
        :param filter_args: Strategy-specific ffmpeg arguments.
        :param output_dir: Directory for saving extracted frames.
        :param start_time: Validated extraction start time.
        :param end_time: Validated extraction end time.
        :param reset_indices: Whether to reset frame numbering.
        """
        command = [
            "ffmpeg",
            "-i", video_path,
            "-ss", str(start_time),
            "-to", str(end_time),
            *filter_args
        ]

        if not reset_indices:
            command.extend(["-frame_pts", "true"])

        command.append(os.path.join(output_dir, "frame_%06d.png"))

        self._run_ffmpeg(command)

        if self.verbose:
            logger.info(f"✔ Frames extracted to '{output_dir}'.")

    @staticmethod
    def _run_ffmpeg(command: list[str]) -> None:
        """
        Execute the provided ffmpeg command.

        :param command: ffmpeg command arguments.
        """
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @staticmethod
    def _validate_avg_fps(metadata: Dict[str, Union[str, float, int]]) -> float:
        """
        Validate and return average FPS from metadata.

        :param metadata: Video metadata.
        :return: Validated average FPS.
        :raises ValueError: If 'avg_fps' is missing or invalid.
        """
        if metadata is None or "avg_fps" not in metadata:
            raise ValueError("Metadata explicitly requires 'avg_fps' key.")

        try:
            avg_fps = float(metadata["avg_fps"])
        except (TypeError, ValueError):
            raise ValueError(f"Invalid 'avg_fps' value in metadata: {metadata.get('avg_fps')}")

        if avg_fps <= 0:
            raise ValueError(f"Invalid 'avg_fps' value: {avg_fps}. Must be positive.")

        return avg_fps

    @staticmethod
    def _validate_time_range(metadata: Dict[str, Union[str, float, int]], start_time: Optional[float],
                             end_time: Optional[float]) -> Tuple[float, float]:
        """
        Validate extraction times against video duration.

        :param metadata: Video metadata with 'duration'.
        :param start_time: Requested extraction start time.
        :param end_time: Requested extraction end time.
        :return: Tuple of validated (start_time, end_time).
        :raises ValueError: If times are invalid.
        """
        if metadata is None or "duration" not in metadata:
            raise ValueError("Metadata explicitly requires valid 'duration' key.")

        duration = float(metadata["duration"])
        if duration <= 0:
            raise ValueError(f"Invalid video duration from metadata: {duration}s.")

        actual_start_time = 0 if start_time is None else start_time
        actual_end_time = duration if end_time is None else end_time

        if actual_start_time < 0 or actual_start_time >= duration:
            raise ValueError(
                f"Start time ({actual_start_time}s) must be within video duration (0s - {duration}s).")

        if actual_end_time <= actual_start_time or actual_end_time > duration:
            raise ValueError(
                f"End time ({actual_end_time}s) must be greater than start time ({actual_start_time}s) "
                f"and within video duration (0s - {duration}s).")

        return actual_start_time, actual_end_time

    @staticmethod
    def _validate_fps(fps: Optional[int]) -> int:
        """
        Validate and return FPS as a positive integer.

        :param fps: Requested frames per second.
        :return: Validated FPS.
        :raises ValueError: If 'fps' is None or non-positive.
        """
        if fps is None:
            raise ValueError("Provided 'fps' parameter is None but is explicitly required.")

        if not isinstance(fps, int) or fps <= 0:
            raise ValueError(f"Invalid 'fps' value: {fps}. Must be a positive integer.")

        return fps


class AllFramesStrategy(FrameExtractionStrategy):
    """
    Extracts all frames using ffmpeg passthrough mode.

    STRATEGY_NAME: "all"
    """
    STRATEGY_NAME = "all"

    def extract_frames(self, video_path: Path, output_dir: Path, fps: Optional[int] = None,
                       start_time: Optional[float] = None, end_time: Optional[float] = None,
                       metadata: Optional[Dict[str, Union[str, float, int]]] = None, reset_indices: bool = False) \
            -> None:
        """
        Extract all frames from the video using passthrough mode.

        :param video_path: Path to the video file.
        :param output_dir: Directory to store extracted frames.
        :param fps: Unused for this strategy (present for interface consistency).
        :param start_time: Extraction start time (seconds).
        :param end_time: Extraction end time (seconds).
        :param metadata: Video metadata (must include duration).
        :param reset_indices: Reset frame indices to start from zero.
        """
        actual_start_time, actual_end_time = self._validate_time_range(metadata, start_time, end_time)

        if self.verbose:
            logger.info("Extracting all frames...")

        self.common_frame_extraction_logic(
            video_path=video_path,
            filter_args=["-fps_mode", "passthrough"],
            output_dir=output_dir,
            start_time=actual_start_time,
            end_time=actual_end_time,
            reset_indices=reset_indices
        )


class UniformFramesStrategy(FrameExtractionStrategy):
    """
    Extracts frames at a uniform rate using the ffmpeg `fps` filter.

    STRATEGY_NAME: "uniform"
    """
    STRATEGY_NAME = "uniform"

    def extract_frames(self, video_path: Path, output_dir: Path, fps: Optional[int] = None,
                       start_time: Optional[float] = None, end_time: Optional[float] = None,
                       metadata: Optional[Dict[str, Union[str, float, int]]] = None, reset_indices: bool = False) \
            -> None:
        """
        Extract frames uniformly at a specified FPS.

        :param video_path: Path to the video file.
        :param output_dir: Directory to store extracted frames.
        :param fps: Frames per second for uniform extraction (required).
        :param start_time: Extraction start time (seconds).
        :param end_time: Extraction end time (seconds).
        :param metadata: Video metadata (must include 'duration' and 'avg_fps').
        :param reset_indices: Reset frame indices to start from zero.
        :raises ValueError: If FPS exceeds video avg_fps.
        """
        fps = self._validate_fps(fps)
        avg_fps = self._validate_avg_fps(metadata)

        if fps > avg_fps:
            raise ValueError(f"Requested FPS ({fps}) exceeds source video FPS ({avg_fps:.2f}).")

        actual_start_time, actual_end_time = self._validate_time_range(metadata, start_time, end_time)

        if self.verbose:
            logger.info(f"Extracting frames at {fps} FPS using 'uniform' sampling...")

        self.common_frame_extraction_logic(
            video_path=video_path,
            filter_args=["-vf", f"fps={fps}"],
            output_dir=output_dir,
            start_time=actual_start_time,
            end_time=actual_end_time,
            reset_indices=reset_indices
        )


class FixedRandomFramesStrategy(FrameExtractionStrategy):
    """
    Extracts a fixed number of random frames using the ffmpeg `select` filter.

    STRATEGY_NAME: "fixed_random"
    """
    STRATEGY_NAME = "fixed_random"

    def extract_frames(self, video_path: Path, output_dir: Path, fps: Optional[int] = None,
                       start_time: Optional[float] = None, end_time: Optional[float] = None,
                       metadata: Optional[Dict[str, Union[float, int]]] = None, reset_indices: bool = False) -> None:
        """
        Extract a specified number of random frames within the given time range.

        :param video_path: Path to the video file.
        :param output_dir: Directory to store extracted frames.
        :param fps: Total number of random frames to extract (required).
        :param start_time: Extraction start time (seconds).
        :param end_time: Extraction end time (seconds).
        :param metadata: Video metadata (must include 'duration' and 'avg_fps').
        :param reset_indices: Reset frame indices to start from zero.
        """
        fps = self._validate_fps(fps)
        avg_fps = self._validate_avg_fps(metadata)

        actual_start_time, actual_end_time = self._validate_time_range(metadata, start_time, end_time)

        if self.verbose:
            logger.info(f"Extracting {fps} random frames from {start_time} to {end_time}...")

        frame_indices = self._select_random_frames(
            fps=fps,
            avg_fps=avg_fps,
            start_time=actual_start_time,
            end_time=actual_end_time
        )

        select_filter = self._build_select_filter(frame_indices)

        self.common_frame_extraction_logic(
            video_path=video_path,
            filter_args=["-vf", f"select='{select_filter}'", "-vsync", "vfr"],
            output_dir=output_dir,
            start_time=actual_start_time,
            end_time=actual_end_time,
            reset_indices=reset_indices
        )

    def _select_random_frames(self, fps: int, avg_fps: float, start_time: Optional[float] = None,
                              end_time: Optional[float] = None) -> List[int]:
        """
        Select random frame indices within the specified time range.

        :param fps: Number of random frames to extract.
        :param avg_fps: Video's average frames per second.
        :param start_time: Validated start time (seconds).
        :param end_time: Validated end time (seconds).
        :return: Sorted list of randomly selected frame indices.
        """
        start_frame = int(start_time * avg_fps)
        end_frame = int(end_time * avg_fps)
        frame_range = end_frame - start_frame

        if frame_range <= 0:
            if self.verbose:
                logger.warning("No valid frame range to extract from.")
            return []

        if frame_range < fps and self.verbose:
            logger.info(f"Requested {fps} frames, but only {frame_range} available. Extracting {frame_range} instead.")

        num_frames_to_extract = min(fps, frame_range)

        samples = sorted(random.sample(range(start_frame, end_frame), num_frames_to_extract))

        return samples

    @staticmethod
    def _build_select_filter(frame_indices: List[int]) -> str:
        """
        Build a ffmpeg select filter from frame indices.

        :param frame_indices: List of frame indices to select.
        :return: ffmpeg-compatible select filter string.
        """
        return "+".join(rf"eq(n\,{idx})" for idx in frame_indices)
