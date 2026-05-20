<img src="internal/icon.png" width="128" height="128" alt="ytdlp-mp3-downloader logo">

# ytdlp-mp3-downloader

A lightweight YouTube audio downloader built for fast, reliable MP3 export. This project focuses on keeping the experience simple and streamlined while preserving high audio quality and basic track metadata for offline listening.

<img src="internal/gui_preview.png" width="500" alt="ytdlp-mp3-downloader gui">

## Features

- Download audio from YouTube at the best available quality (up to 192 kbps)
- Save files as MP3 with metadata sourced from YouTube and iTunes when available
- Simple command-line interface plus a graphical UI entry point
- Session cookies are automatically fetched using `browser-cookie3`. The following browsers are scanned in order, and a `youtube_cookies.txt` file is generated during the session:
  1. Firefox (Tested ✅)
  2. Edge
  3. Brave
  4. Opera
  5. Chrome

## Install

The Python requirements should be installed and `ffmpeg` should be available on the system `PATH`.

```bash
git clone https://github.com/Zigatronz/ytdlp-mp3-downloader
cd ytdlp-mp3-downloader
python -m pip install -r requirements.txt
```

Installation can be verified by running `ffmpeg` in a terminal. If `ffmpeg` is not present, download a build from https://ffmpeg.org/download.html and add it to the system `PATH`.

## Usage

### GUI

```bash
python ytdlp-mp3-downloader-gui.py
```

### CLI

```bash
python ytdlp-mp3-downloader-cli.py --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Flowchart

For a visual overview of the application's workflow, view the [interactive flowchart](https://app.diagrams.net/?src=about#Uhttps%3A%2F%2Fraw.githubusercontent.com%2FZigatronz%2Fytdlp-mp3-downloader%2Frefs%2Fheads%2Fmain%2Fflowchart.drawio).

## Why this project exists

This tool is created for users who want a lightweight, user-friendly way to save YouTube audio as MP3 without dealing with cookies, complex authentication, or heavy setup.

## Dependencies and Licensing

This project is licensed under the **MIT License**.

This project relies on the following third-party libraries, which are installed automatically via your [`requirements.txt`](requirements.txt):

*   [requests](https://github.com/psf/requests) (v2.28.2) – Licensed under the Apache License 2.0
*   [argparse](https://github.com/ThomasWaldmann/argparse/) (v1.4.0) – Licensed under the Python Software Foundation License
*   [music_tag](https://github.com/KristoforMaynard/music-tag) (v0.4.3) – Licensed under the MIT License
*   [yt-dlp](https://github.com/yt-dlp/yt-dlp) (v2026.3.17) – Dedicated to the Public Domain (The Unlicense)
*   [browser-cookie3](https://github.com/borisbabic/browser_cookie3) (v0.19.1) – Licensed under the GNU LGPLv3

All third-party libraries remain the property of their respective authors and are used here under dynamic runtime linking via `pip`.