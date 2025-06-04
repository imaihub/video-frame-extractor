from itertools import product
from pathlib import Path

import pytest

from vfe.frame_extraction_strategy import AllFramesStrategy, UniformFramesStrategy, FixedRandomFramesStrategy
from vfe.video_frame_extractor import VideoFrameExtractor

STRATEGIES = [AllFramesStrategy, UniformFramesStrategy, FixedRandomFramesStrategy]

# Define parameter spaces
video_valid_flags = [True, False]
output_valid_flags = [True, False]
reset_flags = [True, False]
fps_values = [None, 0, 25, 50]
start_end_combinations = [
    (None, None),  # default
    (0, None),  # valid range
    (None, 1),  # valid range
    (0, 1),  # valid range
    (-1, 1),  # invalid start
    (0, -1),  # invalid end
    (1, 0),  # start beyond end
    (0, 2),  # end beyond duration
]


@pytest.mark.parametrize("strategy_cls,video_valid,output_valid,fps,reset_indices, start_end_combinations",
                         list(product(STRATEGIES, video_valid_flags, output_valid_flags, fps_values, reset_flags,
                                      start_end_combinations)))
def test_extraction_combinatoric(tmp_path: Path, strategy_cls, video_valid: bool, output_valid: bool, fps: int,
                                 reset_indices: bool, start_end_combinations: tuple) -> None:
    """
    Test all combinations of strategy, fps, time, validity flags, and reset indices.

    :param tmp_path: Temporary output path.
    :return: None
    """
    start_time, end_time = start_end_combinations

    video_path = Path("tests/data/sample.mp4") if video_valid else tmp_path / "missing.mp4"
    output_path = tmp_path if output_valid else Path("/invalid/output/path")

    strategy = strategy_cls()

    extractor_args = {
        "video_path": video_path,
        "output_dir": output_path,
        "fps": fps,
        "start_time": start_time,
        "end_time": end_time,
        "strategy": strategy,
        "reset_indices": reset_indices,
    }

    expects_failure = (
            not video_path.exists()
            or not output_valid
            or (fps is None and strategy_cls is not AllFramesStrategy)
            or (fps is not None and fps <= 0)
            or (start_time is not None and start_time < 0)
            or (end_time is not None and end_time < 0)
            or (start_time is not None and end_time is not None and end_time <= start_time)
            or (start_time is not None and start_time > 1.0)
            or (end_time is not None and end_time > 1.0)
            or (strategy_cls is UniformFramesStrategy and fps > 25)
    )

    if expects_failure:
        with pytest.raises((ValueError, FileNotFoundError, OSError)) as exc_info:
            extractor = VideoFrameExtractor(**extractor_args)
            extractor.extract_frames()
    else:
        extractor = VideoFrameExtractor(**extractor_args)
        extractor.extract_frames()
        frames = list(output_path.glob("*.png"))
        assert isinstance(frames, list)


def test_extractor_metadata(tmp_path: Path) -> None:
    """
    Test that metadata can be retrieved from the extractor.

    :param tmp_path: Temporary output path.
    :return: None
    """
    video_path = Path("tests/data/sample.mp4")
    strategy = AllFramesStrategy()

    extractor = VideoFrameExtractor(
        video_path=video_path,
        output_dir=tmp_path,
        fps=10,
        strategy=strategy,
        verbose=False
    )

    metadata = extractor.get_metadata()
    if metadata:
        assert "codec" in metadata
        assert "duration" in metadata
        assert metadata["duration"] > 0
