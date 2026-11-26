import argparse
import sys
from internal.logger import get_logger

logger = get_logger(__name__)
from internal.download import download

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
    logger.info(f"Start downloading using CLI: {url}")
    dn = download()
    try:
        dn.download(url=url)
        logger.info(f"Download completed successfully.")
        exit(0)
    except:
        logger.error(f"An error occurred during download.")
        exit(1)

if __name__ == "__main__":
    main()
