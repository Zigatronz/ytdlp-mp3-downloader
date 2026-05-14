<img src="internal/icon.png" width="128" height="128" alt="ytdlp-mp3-downloader logo">

# ytdlp-mp3-downloader

A lightweight YouTube audio downloader built for fast, reliable MP3 export. This project focuses on keeping the experience simple and streamlined while preserving high audio quality and basic track metadata for offline listening.

## Features

- Download audio from YouTube at the best available quality (up to 192 kbps)
- Save files as MP3 with metadata sourced from YouTube and iTunes when available
- Simple command-line interface plus a graphical UI entry point
- No cookie management or complex configuration required

## Install

```bash
git clone https://github.com/Zigatronz/ytdlp-mp3-downloader
cd ytdlp-mp3-downloader
python -m pip install -r requirements.txt
```

## Usage

### GUI

```bash
python ytdlp-mp3-downloader-gui.py
```

### CLI

```bash
python ytdlp-mp3-downloader-cli.py --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Why this project exists

This tool is created for users who want a lightweight, user-friendly way to save YouTube audio as MP3 without dealing with cookies, complex authentication, or heavy setup.

## License

This project is distributed under the MIT License. You are free to use, modify, and distribute the code with attribution, subject to the terms of the MIT License.
