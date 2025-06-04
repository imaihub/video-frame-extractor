from pathlib import Path

import pytest

from vfe.frame_extraction_strategy import AllFramesStrategy
from vfe.utils import validate_output_path, get_strategy_class


class TestValidateOutputPath:
    def test_validate_output_path_creates(self, tmp_path: Path) -> None:
        """Test that validate_output_path creates the directory if it doesn't exist."""
        target: Path = tmp_path / "output"
        result: Path = validate_output_path(target)
        assert result.exists()
        assert result.is_dir()

    def test_validate_output_path_raises_when_missing_and_no_create(self, tmp_path: Path) -> None:
        """Test that validate_output_path raises if dir doesn't exist and create_if_missing is False."""
        target: Path = tmp_path / "missing_dir"
        with pytest.raises(FileNotFoundError):
            validate_output_path(target, create_if_missing=False)

    def test_validate_output_path_existing(self, tmp_path: Path) -> None:
        """Test that validate_output_path returns the path if it already exists."""
        result: Path = validate_output_path(tmp_path)
        assert result == tmp_path
        assert result.exists()


class TestGetStrategyClass:
    def test_get_strategy_class_valid(self) -> None:
        """Test that a valid strategy name returns the correct class."""
        strategy = get_strategy_class("all")
        assert issubclass(strategy, AllFramesStrategy)

    def test_get_strategy_class_case_insensitive(self) -> None:
        """Test that strategy lookup is case-insensitive."""
        strategy = get_strategy_class("AlL")
        assert issubclass(strategy, AllFramesStrategy)

    def test_get_strategy_class_invalid(self) -> None:
        """Test that an invalid strategy name raises ValueError."""
        with pytest.raises(ValueError):
            get_strategy_class("invalid_strategy")
