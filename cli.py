import argparse
import logging
from pathlib import Path
from typing import Optional

from vfe.frame_extraction_strategy import FrameExtractionStrategy
from vfe.logging_config import configure_vfe_logging
from vfe.utils import VALID_VIDEO_EXTENSIONS, get_strategy_class
from vfe.video_frame_extractor import VideoFrameExtractor

logger = logging.getLogger(__name__)


class VideoFrameExtractorCLI:
    """
    Command-line interface for extracting frames from videos and retrieving metadata.
    """
    VALID_EXTS = VALID_VIDEO_EXTENSIONS

    def __init__(self) -> None:
        """
        Initialize the VideoFrameExtractorCLI and parse CLI arguments.

        :return: None
        :raises argparse.ArgumentError: If invalid arguments are passed.
        :raises ValueError: If video_path or output_dir cannot be interpreted as valid paths.
        """
        self.parser = argparse.ArgumentParser(
            description="CLI for extracting frames and retrieving metadata from videos."
        )
        subparsers = self.parser.add_subparsers(
            dest="command",
            required=True,
            help="Command to run (extract | metadata)."
        )

        # Extract command
        extract_parser = subparsers.add_parser(
            "extract",
            help="Extract frames from video"
        )
        extract_parser.add_argument(
            "--strategy",
            help="Frame extraction strategy (e.g., all, uniform, fixed_random)"
        )
        extract_parser.add_argument(
            "--video_path",
            required=True,
            help="Path to the input video file or a directory containing video files "
                 "(Allowed extensions (unless --allow_any_extension is used): .mp4, .avi, .mov, .mkv, .webm)."
                 "If a directory is provided, all supported videos will be processed and their frames will be saved "
                 "in separate subdirectories named after each video file."
        )
        extract_parser.add_argument(
            "--allow_any_extension",
            action="store_true",
            help="Allow any file extension. When set, all files are passed to ffmpeg regardless of extension."
        )
        extract_parser.add_argument(
            "--output_dir",
            required=True,
            help="Directory to save extracted frames"
        )
        extract_parser.add_argument(
            "--fps",
            type=int,
            help="Frames per second"
        )
        extract_parser.add_argument(
            "--start_time",
            type=float,
            default=0,
            help="Start time for extraction"
        )
        extract_parser.add_argument(
            "--end_time",
            type=float,
            help="End time for extraction"
        )
        extract_parser.add_argument(
            "--reset_indices",
            action="store_true",
            help="Reset frame numbering in output (starts at 0 instead of using original frame numbers)"
        )
        extract_parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose logging"
        )

        # Metadata command
        metadata_parser = subparsers.add_parser(
            "metadata",
            help="Display video metadata"
        )
        metadata_parser.add_argument(
            "--video_path",
            required=True,
            help="Path to the input video file or a directory containing video files "
                 "(Allowed extensions (unless --allow_any_extension is used): .mp4, .avi, .mov, .mkv, .webm)."
                 "If a directory is provided, all supported videos will be processed and their frames will be saved "
                 "in separate subdirectories named after each video file."
        )
        metadata_parser.add_argument(
            "--allow_any_extension",
            action="store_true",
            help="Allow any file extension. When set, all files are passed to ffmpeg regardless of extension."
        )
        metadata_parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose logging"
        )

        self.args = self.parser.parse_args()
        self.args.video_path = Path(self.args.video_path)
        if "output_dir" in self.args:
            self.args.output_dir = Path(self.args.output_dir)

    def get_strategy(self) -> Optional[FrameExtractionStrategy]:
        """
        Retrieve the frame extraction strategy instance based on CLI argument.

        :return: FrameExtractionStrategy instance or None to fallback to default in VideoFrameExtractor.
        :raises ValueError: If a strategy requires --fps and it's missing.
        """
        if not self.args.strategy:
            return None
        strategy_cls = get_strategy_class(self.args.strategy)

        if self.args.strategy != "all" and self.args.fps is None:
            raise ValueError(f"The '{self.args.strategy}' strategy explicitly requires --fps to be specified.")

        return strategy_cls(verbose=self.args.verbose)

    def extract_frames(self) -> None:
        """
        Extract frames from a single video or all videos in a directory.

        :return: None
        :raises FileNotFoundError: If the provided path is invalid.
        :raises ValueError: If a file has an unsupported extension.
        """
        strategy = self.get_strategy()
        video_path = self.args.video_path
        output_dir = self.args.output_dir

        if video_path.is_file():
            if not self.args.allow_any_extension and video_path.suffix.lower() not in self.VALID_EXTS:
                raise ValueError(f"Unsupported video format: {video_path.suffix}")

            extractor = VideoFrameExtractor(
                video_path=video_path,
                output_dir=output_dir,
                fps=self.args.fps,
                start_time=self.args.start_time,
                end_time=self.args.end_time,
                strategy=strategy,
                reset_indices=self.args.reset_indices,
                verbose=self.args.verbose
            )
            extractor.extract_frames()

        elif video_path.is_dir():
            for vid_file in video_path.iterdir():
                if vid_file.suffix.lower() in self.VALID_EXTS:
                    sub_output = output_dir / vid_file.stem
                    sub_output.mkdir(parents=True, exist_ok=True)
                    extractor = VideoFrameExtractor(
                        video_path=vid_file,
                        output_dir=sub_output,
                        fps=self.args.fps,
                        start_time=self.args.start_time,
                        end_time=self.args.end_time,
                        strategy=strategy,
                        reset_indices=self.args.reset_indices,
                        verbose=self.args.verbose
                    )
                    extractor.extract_frames()
                else:
                    logger.warning(f"[VFE] Skipping unsupported file: {vid_file.name}")
        else:
            raise FileNotFoundError(f"Invalid path: {video_path}")

    def get_metadata(self) -> None:
        """
        Retrieve and display metadata from a single video or all videos in a directory.

        :return: None
        :raises ValueError: If a file has an unsupported extension.
        """
        video_path = self.args.video_path

        if video_path.is_file():
            if not self.args.allow_any_extension and video_path.suffix.lower() not in self.VALID_EXTS:
                raise ValueError(f"Unsupported video format: {video_path.suffix}")

            extractor = VideoFrameExtractor(
                video_path=video_path,
                strategy=None,
                verbose=self.args.verbose
            )
            metadata = extractor.get_metadata()
            if metadata:
                logger.info(f"\nVideo Metadata for {video_path.name}:")
                for key, value in metadata.items():
                    logger.info(f"{key.title()}: {value}")

        elif video_path.is_dir():
            for vid_file in video_path.iterdir():
                if vid_file.suffix.lower() in self.VALID_EXTS:
                    extractor = VideoFrameExtractor(
                        video_path=vid_file,
                        strategy=None,
                        verbose=self.args.verbose
                    )
                    metadata = extractor.get_metadata()
                    if metadata:
                        logger.info(f"\nVideo Metadata for {vid_file.name}:")
                        for key, value in metadata.items():
                            logger.info(f"{key.title()}: {value}")
                else:
                    logger.warning(f"[VFE] Skipping unsupported file: {vid_file.name}")

    def run(self) -> None:
        """
        Execute the appropriate command based on the parsed arguments.
        """
        configure_vfe_logging(self.args.verbose)

        if self.args.command == "extract":
            self.extract_frames()
        elif self.args.command == "metadata":
            self.get_metadata()


def main() -> None:
    """
    Entry point for the VideoFrameExtractorCLI.
    """
    cli = VideoFrameExtractorCLI()
    cli.run()


if __name__ == "__main__":
    main()
