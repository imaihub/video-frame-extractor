import os
from pathlib import Path

from vfe.frame_extraction_strategy import AllFramesStrategy, UniformFramesStrategy, FixedRandomFramesStrategy
from vfe.video_frame_extractor import VideoFrameExtractor


def run_extraction(video_path: str, allow_any_extension: bool, output_dir: str, fps: int, strategy_name: str,
                   start_time: float = None, end_time: float = None, reset_indices: bool = False, verbose: bool = True
                   ) -> None:
    """
    Run frame extraction using the given parameters.
    """
    os.makedirs(output_dir, exist_ok=True)

    strategy_cls = {
        "all": AllFramesStrategy,
        "uniform": UniformFramesStrategy,
        "fixed_random": FixedRandomFramesStrategy,
    }.get(strategy_name)

    if not strategy_cls:
        raise ValueError(f"Unsupported strategy: {strategy_name}")

    strategy = strategy_cls(verbose=verbose)

    extractor = VideoFrameExtractor(
        video_path=Path(video_path),
        allow_any_extension=allow_any_extension,
        output_dir=Path(output_dir),
        fps=fps,
        start_time=start_time,
        end_time=end_time,
        strategy=strategy,
        reset_indices=reset_indices,
        verbose=verbose
    )

    extractor.extract_frames()


def run_metadata(video_path: str, allow_any_extension: bool = False, verbose: bool = True) -> None:
    """
    Retrieve and print video metadata.
    """
    extractor = VideoFrameExtractor(
        video_path=Path(video_path),
        allow_any_extension=allow_any_extension,
        verbose=verbose
    )
    metadata = extractor.get_metadata()
    if metadata:
        print("\n[Metadata]")
        for key, value in metadata.items():
            print(f"{key.title()}: {value}")


if __name__ == "__main__":
    MODE = "extract"  # change to "metadata" as needed

    if MODE == "extract":
        run_extraction(
            video_path="/path/to/video.mp4",
            allow_any_extension=False,
            output_dir="/path/to/output",
            fps=1,
            strategy_name="uniform",
            start_time=0,
            end_time=10,
            reset_indices=True,
            verbose=True
        )
    elif MODE == "metadata":
        run_metadata(
            video_path="/path/to/video.mp4",
            allow_any_extension=False,
            verbose=True
        )
