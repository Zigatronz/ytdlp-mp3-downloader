import argparse
import sys
from internal.download_mp3 import download_mp3
from internal.better_filename import better_filename
from internal.metadata_fetcher import itunes_metadata_fetcher
from internal.metadata_json import append_metadata
from internal.mp3_metadata import Mp3Metadata
from internal.log_time import logTime
from pathlib import Path
import os

def _configure_io_encoding():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def main():
    _configure_io_encoding()
    parser = argparse.ArgumentParser(description="Download mp3 with metadata from YouTube.")
    parser.add_argument("--url", required=True, help="URL of YouTube video/music.")
    args = parser.parse_args()
    url = args.url
    output_folder = "Music"
    metadata_json = "download_history.json"

    if not ( url.startswith("https://www.youtube.com/") or url.startswith("https://youtu.be/") or url.startswith("https://music.youtube.com/") ):
        logTime("Invalid URL. Please provide a valid YouTube video URL.", level="ERR")
        exit(1)
    
    # 1. Download the mp3 file
    try:
        os.makedirs(output_folder, exist_ok=True)
        logTime(f"Downloading from URL: {url}", level="INF")
        metadata_yt = download_mp3(url, output_folder=output_folder)
        logTime(f"Download completed successfully. " + Path(metadata_yt.file_path).stem, level="INF")
    except Exception as e:
        logTime(f"An error occurred during download: {e}", level="ERR")
        exit(2)
    
    # 2. Clean up the filename
    # try:
    #     logTime(f"Cleaning filename: {Path(music_path).name}", level="INF")
    #     new_music_path = better_filename(music_path)
    #     os.rename(music_path, new_music_path)
    #     music_path = new_music_path
    #     logTime(f"Filename cleaned: {Path(music_path).name}", level="INF")
    # except Exception as e:
    #     logTime(f"An error occurred while renaming the file: {e}", level="ERR")

    # 3. Fetch and apply metadata
    try:
        search_query = [
            metadata_yt.song_title,
            f"{metadata_yt.yt_uploader} - {metadata_yt.song_title}",
        ]
        
        song_title = Path(metadata_yt.song_title).stem
        meta_fetcher = itunes_metadata_fetcher(song_title, metadata_from_yt=metadata_yt)

        try:
            logTime(f"Fetching metadata from iTunes API for: {Path(music_path).stem}", level="INF")
            metadata_itunes = meta_fetcher.fetch()
            logTime("Metadata fetched successfully.", level="INF")
        except Exception as e:
            logTime(f"Metadata fetch failed: {e}", level="ERR")
            metadata_itunes = Mp3Metadata()

        if not metadata_itunes.song_title:
            metadata_itunes.song_title = song_title
        if not metadata_itunes.artist:
            metadata_itunes.artist = metadata_yt["uploader"]
        if not metadata_itunes.year:
            metadata_itunes.year = metadata_yt["upload_date_year"]
        metadata_itunes.comment = metadata_yt["webpage_url"]

        logTime(f"Applying metadata to: {Path(music_path).name}", level="INF")
        metadata_itunes.save_to_file(music_path)
        logTime("Metadata applied.", level="INF")

        file_key = metadata_yt.get("video_id", Path(music_path).name)
        append_metadata(
            metadata_json,
            file_key,
            "ITunes",
            metadata_itunes.to_json_friendly(),
            os.path.dirname(music_path),
            os.path.basename(music_path)
        )
        logTime(f"iTunes metadata written to JSON file: {metadata_json}", level="INF")
    except Exception as e:
        logTime(f"An error occurred while fetching/applying metadata: {e}", level="ERR")
    finally:
        logTime("Task completed:", level="INF")
        logTime(f"{Path(music_path).name}", level="INF")

if __name__ == "__main__":
    main()
    exit(0)
