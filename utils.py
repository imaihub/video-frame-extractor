import logging
from pathlib import Path

from vfe.frame_extraction_strategy import FrameExtractionStrategy

logger = logging.getLogger(__name__)

VALID_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


# ------------------------------------------------------------------
# Strategy resolution utilities
# ------------------------------------------------------------------
def get_strategy_class(name: str) -> type[FrameExtractionStrategy]:
    """
    Resolve a FrameExtractionStrategy subclass by STRATEGY_NAME (case-insensitive).

    :param name: Strategy name (e.g., "all", "uniform", "fixed_random").
    :return: Matching FrameExtractionStrategy subclass.
    :raises ValueError: If no matching strategy class is found.
    """
    name = name.lower()
    for cls in FrameExtractionStrategy.__subclasses__():
        if hasattr(cls, "STRATEGY_NAME") and cls.STRATEGY_NAME == name:
            return cls
    raise ValueError(f"No strategy found for name: {name}")


# ------------------------------------------------------------
# General utility functions (e.g., paths, filesystem handling)
# ------------------------------------------------------------
def validate_output_path(output_dir: Path, create_if_missing: bool = True) -> Path:
    """
    Ensure the output directory exists, or optionally create it.

    :param output_dir: The path of the directory to validate.
    :param create_if_missing: Whether to automatically create the directory if it does not exist.
    :return: A valid output directory path.
    :raises FileNotFoundError: If the directory does not exist and creation is disabled.
    :raises NotADirectoryError: If the path exists but is not a directory.
    :raises OSError: If directory creation fails.
    """
    if output_dir.exists():
        if not output_dir.is_dir():
            raise NotADirectoryError(f"Output path exists but is not a directory: {output_dir}")
        return output_dir

    logger.warning(f"Output directory '{output_dir}' does not exist.")

    if create_if_missing:
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✔ Created output directory: {output_dir}")
            return output_dir
        except OSError as e:
            logger.error(f"Failed to create output directory: {e}")
            raise OSError(f"Failed to create output directory: {output_dir}") from e
    else:
        logger.error(f"Output directory '{output_dir}' does not exist and create_if_missing=False.")
        raise FileNotFoundError(f"Output directory '{output_dir}' does not exist and create_if_missing=False.")
