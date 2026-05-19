import argparse
from internal.download_mp3 import download_mp3
from internal.better_filename import better_filename
from internal.metadata_fetcher import metadata_fetcher
from pathlib import Path
import os

def main():
    parser = argparse.ArgumentParser(description="Download mp3 with metadata from YouTube.")
    parser.add_argument("--url", required=True, help="URL of YouTube video/music.")
    args = parser.parse_args()
    url = args.url
    metadata = None

    if not ( url.startswith("https://www.youtube.com/") or url.startswith("https://youtu.be/") or url.startswith("https://music.youtube.com/") ):
        print("Invalid URL. Please provide a valid YouTube video URL.")
        exit(1)

    output_folder = "Music"
    
    # 1. Download the mp3 file
    try:
        os.makedirs(output_folder, exist_ok=True)
        print(f"Downloading from URL: {url}")
        music_path, metadata = download_mp3(url, output_folder=output_folder)
        print(f"\nDownload completed successfully: {Path(music_path).name}")
    except Exception as e:
        print(f"An error occurred during download: {e}")
        exit(2)
    
    # 2. Clean up the filename
    try:
        print(f"Cleaning filename: {Path(music_path).name}")
        new_music_path = better_filename(music_path)
        os.rename(music_path, new_music_path)
        music_path = new_music_path
        print(f"Filename cleaned: {Path(music_path).name}")
    except Exception as e:
        print(f"An error occurred while renaming the file: {e}")

    # 3. Fetch and apply metadata
    try:
        song_title = Path(music_path).stem
        meta_fetcher = metadata_fetcher(song_title)

        # fill existing metadata with title from download if available
        print(f"Using metadata from download as base.")
        meta_fetcher.metadata["title"] = song_title
        meta_fetcher.metadata["artist"] = metadata["uploader"]
        meta_fetcher.metadata["year"] = metadata["upload_date_year"]
        meta_fetcher.metadata["comment"] = metadata["webpage_url"] # Store the original URL in the comment tag
        meta_fetcher.metadata["artwork_url"] = metadata["thumbnail_url"]

        try:
            print(f"Fetching metadata from iTunes API for: {Path(music_path).stem}")
            meta_fetcher.fetch()
            print("Metadata fetched successfully.")
        # except ValueError as e:
        #     print(f"Metadata fetch failed: {e}")
        #     print("Retrying with cleaned title...")
        #     meta_fetcher.song_title = song_title.replace(metadata["uploader"], "").strip()
        #     meta_fetcher.fetch()
        #     print("Metadata fetched successfully.")
        #     print("Renaming file based on fetched metadata...")
        #     new_music_name = f"{meta_fetcher.metadata['artist']} - {meta_fetcher.metadata['title']}{Path(music_path).suffix}"
        #     new_music_path = os.path.join(Path(music_path).parent, new_music_name)
        #     os.rename(music_path, new_music_path)
        #     music_path = new_music_path
        #     print(f"File renamed to: {Path(music_path).name}")
        except Exception as e:
            print(f"Metadata fetch failed: {e}")
        finally:
            print(f"Applying metadata to: {Path(music_path).name}")
            meta_fetcher.apply_metadata(music_path)
            print("Metadata applied.")
    except Exception as e:
        print(f"An error occurred while fetching/applying metadata: {e}")
    finally:
        print(f"Task completed:")
        print(f"    {Path(music_path).name}")

if __name__ == "__main__":
    main()
    exit(0)
