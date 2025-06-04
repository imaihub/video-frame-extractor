import sys
from unittest import mock

import pytest

from vfe.cli import main as cli_main


@pytest.mark.parametrize("argv, expected_method", [
    # Valid extract command with all required args
    ([
         "cli.py", "extract",
         "--video_path", "tests/data/sample.mp4",
         "--output_dir", "tests/output",
         "--fps", "1",
         "--start_time", "0",
         "--strategy", "all",
         "--reset_indices"
     ], "extract_frames"),
    # Minimal valid extract command (only required args)
    ([
         "cli.py", "extract",
         "--video_path", "tests/data/sample.mp4",
         "--output_dir", "tests/output",
     ], "extract_frames"),
    # Minimal valid extract command (only required args)
    ([
         "cli.py", "extract",
         "--video_path", "tests/data/sample.mp4",
         "--output_dir", "tests/output",
         "--strategy", "uniform",
         "--fps", "5"
     ], "extract_frames"),
    # Valid extract command with only strategy
    ([
         "cli.py", "extract",
         "--video_path", "tests/data/sample.mp4",
         "--output_dir", "tests/output"
     ], "extract_frames"),

    # Valid metadata command with just required video path
    ([
         "cli.py", "metadata",
         "--video_path", "tests/data/sample.mp4"
     ], "get_metadata"),
    # Missing --output_dir for extract (should raise SystemExit)
    ([
         "cli.py", "extract",
         "--video_path", "tests/data/sample.mp4"
     ], "SystemExit"),
    # Missing --fps for strategy 'uniform' (should raise ValueError)
    ([
         "cli.py", "extract",
         "--video_path", "tests/data/sample.mp4",
         "--output_dir", "tests/output",
         "--strategy", "uniform"
     ], "ValueError"),

    # Missing --video_path for metadata (should raise SystemExit)
    ([
         "cli.py", "metadata"
     ], "SystemExit"),
    ([
         "cli.py", "extract",
         "--video_path", "tests/data/sample.mp4",
         "--output_dir", "tests/output",
         "--fps", "1",
         "--extra_arg", "oops"
     ], "SystemExit"),
    # Extract-only arguments passed to metadata (should raise SystemExit)
    ([
         "cli.py", "metadata",
         "--video_path", "tests/data/sample.mp4",
         "--fps", "10",
         "--start_time", "5"
     ], "SystemExit"),
    # Output_dir passed to metadata (not accepted, should raise SystemExit)
    ([
         "cli.py", "metadata",
         "--video_path", "tests/data/sample.mp4",
         "--output_dir", "tests/unused"
     ], "SystemExit")
])
@mock.patch("vfe.cli.VideoFrameExtractor.extract_frames")
@mock.patch("vfe.cli.VideoFrameExtractor.get_metadata", return_value={"codec": "h264", "duration": 1.0})
def test_cli_command_dispatch(mock_metadata, mock_extract, argv, expected_method, monkeypatch):
    """
    Test that CLI dispatches to the correct method based on the command.

    :param mock_metadata: Mocked metadata method.
    :param mock_extract: Mocked extract method.
    :param argv: Command-line arguments.
    :param expected_method: Method name expected to be called.
    """
    monkeypatch.setattr(sys, "argv", argv)
    if expected_method == "SystemExit":
        with pytest.raises(SystemExit):
            cli_main()
        return

    if expected_method == "ValueError":
        with pytest.raises(ValueError):
            cli_main()
        return

    cli_main()

    if expected_method == "extract_frames":
        mock_extract.assert_called_once()
    elif expected_method == "get_metadata":
        mock_metadata.assert_called()
