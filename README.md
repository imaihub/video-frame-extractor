# Video Frame Extractor

A Python package and CLI tool based on FFmpeg for extracting frames from video files using customizable strategies, and for retrieving
detailed video metadata.

---

## Features

- Extract frames from a single video or a directory of videos.
- Choose from multiple frame extraction strategies:
    - `all`: extract every frame
    - `uniform`: extract frames evenly across the video
    - `fixed_random`: extract a fixed number of frames at random
- Retrieve video metadata using `ffprobe`
- Supports `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm` formats
- Built-in CLI with verbose logging option

---

## Installation

### 1. Clone this repository

```bash
git clone https://github.com/imaihub/video-frame-extractor.git
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install FFmpeg and FFprobe
This tool relies on [FFmpeg](https://ffmpeg.org/) for video decoding, therefore you must have `ffmpeg` and `ffprobe` 
installed and added to your system `PATH`.

```bash
sudo apt install ffmpeg
```

Check installation:

```bash
ffmpeg -version
ffprobe -version
```

---

## Usage

### From CLI

Note: the examples below use singular videos, but also work with complete directories with multiple videos.

#### Extract Frames from a Video (All Frames):

```bash
python cli extract --video_path path/to/video.mp4 --output_dir path/to/frames --strategy all
```

#### Extract Frames from a Video (Uniform Sampling):

```bash
python cli extract --video_path path/to/video.mp4 --output_dir path/to/frames --strategy uniform --fps 1
```

#### Extract Frames from a Video (Random Sampling):

```bash
python cli extract --video_path path/to/video.mp4 --output_dir path/to/frames --strategy fixed_random --fps 10
```

#### Retrieve Metadata:

```bash
python main.py metadata --video_path path/to/video.mp4
```

### Optional Flags

#### Video Frame Extraction
- `--start_time`, `--end_time` – limit the extraction window 
- `--allow_any_extension` – process all files regardless of extension

#### Video Frame Extraction or Metadata Retrieval
- `--reset_indices` – reset frame numbering starting at 0
- `--verbose` – enable detailed logging

---

## Testing

To run tests:

```bash
pytest
```

Tests cover:

- Frame extraction logic
- CLI behavior
- Utility functions

---

## Project Structure

```
vfe/
├── __init__.py
├── cli.py
├── frame_extraction_strategy.py
├── logging_config.py
├── main.py
├── utils.py
├── video_frame_extractor.py

├── tests/
│   ├── __init__.
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_extractor.py
│   └── test_utils.py

├── LICENSE.md
├── README.md
├── requirements.txt
```

---

## License

This project is released under the [AGPL 3.0 License](LICENSE.md).