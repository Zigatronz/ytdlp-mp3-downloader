import yt_dlp
import time, browser_cookie3, os
import logging
from internal.logger import get_logger

logger = get_logger(__name__)
from internal.metadata_struct import Metadata_YouTube
from datetime import datetime
from internal.settings import get_settings
from pathlib import Path
import inspect

def scrape_youtube_cookies() -> None:
    """
    Extracts browser session cookies natively and writes them to a 
    standardized Netscape text format that yt-dlp strictly expects.
    """
    PIPELINE = inspect.currentframe().f_code.co_name
    setting = get_settings()
    cookie_file = Path.cwd() / setting["yt_downloader"]["cookie_file"]

    browser_functions = [
        ('Firefox', browser_cookie3.firefox),
        ('Edge', browser_cookie3.edge),
        ('Brave', browser_cookie3.brave),
        ('Opera', browser_cookie3.opera),
        ('Chrome', browser_cookie3.chrome),
    ]

    combined_jar = None
    got_cookies = False
    for name, fetch_function in browser_functions:
        try:
            cookies = fetch_function(domain_name='.youtube.com')
            if cookies is None:
                continue

            if combined_jar is None:
                combined_jar = cookies
            else:
                for cookie in cookies:
                    combined_jar.set_cookie(cookie)
            got_cookies = True
            logger.info(f"Scraped active session tokens from: {name}")
        except Exception:
            logger.log(logging.INFO if ("INF" if got_cookies else "WRN") == 'INF' else (logging.WARNING if ("INF" if got_cookies else "WRN") == 'WRN' else logging.ERROR), f"Failed to scrape active session tokens from: {name}")
            continue

    if combined_jar is None:
        logger.error("Failed to scrape active session tokens from any browser.")
        raise Exception("Failed to scrape active session tokens from any browser.")

    # Compile memory blocks into Netscape text file layout
    cookie_file_content = (
        "# Netscape HTTP Cookie File\n"
        "# http://curl.haxx.se/rfc/cookie_spec.html\n"
        "# This is a generated file! Do not edit.\n\n"
    )
    
    for cookie in combined_jar:
        domain = str(cookie.domain)
        include_subdomains = "TRUE" if domain.startswith(".") else "FALSE"
        path = str(cookie.path)
        secure = "TRUE" if cookie.secure else "FALSE"
        expires = str(cookie.expires) if cookie.expires is not None else str(int(time.time()) + 31536000)
        name = str(cookie.name)
        value = str(cookie.value)
        
        cookie_file_content += f"{domain}\t{include_subdomains}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n"

    with open(cookie_file, "w", encoding="utf-8") as f:
        f.write(cookie_file_content)

    return True


def make_hook(progress_callback : callable):
    """
    Creates a custom yt-dlp hook that forwards data to Flet.
    """
    def custom_hook(d):
        if d['status'] == 'downloading':
            percent_str = d.get('_percent_str', '0%').replace('%', '').strip()
            try:
                percent = float(percent_str)
                progress_callback(f"Downloading {percent:.0f}%")
            except ValueError:
                pass
        elif d['status'] == 'finished':
            progress_callback("Converting...")
    return custom_hook

def get_video_id(url):
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get('id')

def ytdlp(url: str, progress_callback : callable = None) -> Metadata_YouTube:
    PIPELINE = "ytdlp"
    setting = get_settings()
    cookie_file = setting["yt_downloader"]["cookie_file"]
    output_folder = setting["app"]["download_folder"]
    metadata = Metadata_YouTube()

    if os.path.exists(cookie_file):
        logger.info("Existing cookie file found. Using it for authentication.")
        has_cookies = True
    else:
        try:
            has_cookies = bool(scrape_youtube_cookies())
        except Exception:
            has_cookies = False

    ydl_params = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_folder}/%(uploader)s - %(title)s.%(ext)s',
        'writethumbnail': True,
        'allowed_extractors': ['default'],
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            },
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True,   # Automatically injects Title, Artist, etc., into MP3 tags
            },
            {
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': True,
            }
        ],
        'extract_flat': False,
        'noplaylist': True,
        'quiet': False,
    }

    if progress_callback:
        ydl_params['quiet'] = True
        ydl_params['progress_hooks'] = [make_hook(progress_callback)]
    
    if has_cookies and os.path.exists(cookie_file):
        ydl_params['cookiejar'] = cookie_file
        
        # Force yt-dlp to use the standard desktop web player clients
        # This prevents YouTube from serving DRM-protected TV/Mobile streams to the account.
        ydl_params['extractor_args'] = {
            'youtube': {
                'player_client': ['web', 'android'],
                'player_js_variant': ['web']
            }
        }
        
        # Mimic a standard Windows Firefox browser to align perfectly with cookies
        ydl_params['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    else:
        logger.warning("No browser tokens generated. Defaulting to standard stream request.")

    try:
        if progress_callback:
            progress_callback("Downloading...")
        logger.info(f"Starting download for URL: {url}")
        with yt_dlp.YoutubeDL(ydl_params) as ydl:
            start_time = time.time()
            info_dict = ydl.extract_info(url, download=True)
            if isinstance(info_dict, dict) and info_dict.get('entries'):
                info_dict = next((entry for entry in info_dict['entries'] if entry), info_dict)
            requested_downloads = info_dict.get('requested_downloads', [])
            
            if requested_downloads:
                final_path = requested_downloads[-1].get('filepath')
            else:
                final_path = info_dict.get('_filename')

            metadata.file_path = final_path
            metadata.id = info_dict.get('id')
            metadata.title = info_dict.get('title')
            metadata.track = info_dict.get('track')
            metadata.uploader = info_dict.get('uploader')
            metadata.artist = info_dict.get('artist')
            metadata.album = info_dict.get('album')
            metadata.album_artist = info_dict.get('album_artist')
            metadata.genre = info_dict.get('genre')
            metadata.release_year = info_dict.get('release_year')
            metadata.creators = info_dict.get('creators')
            metadata.duration = info_dict.get('duration')
            metadata.view_count = info_dict.get('view_count')
            metadata.description = info_dict.get('description')
            upload_date_str = info_dict.get('upload_date')
            if upload_date_str:
                try:
                    metadata.upload_date = datetime.strptime(upload_date_str, '%Y%m%d')
                except ValueError:
                    metadata.upload_date = None
            metadata.url = info_dict.get('webpage_url')
            metadata.artwork_url = info_dict.get('thumbnail')

            # get local thumbnail instead if exists
            thumb_exts = [
                '.png',
                '.jpg',
                '.jpeg',
                '.webp',
            ]
            base_path = Path(metadata.file_path).resolve()
            for ext in thumb_exts:
                thumb_path = base_path.with_suffix(ext)
                if thumb_path.is_file():
                    metadata.artwork_url = str(thumb_path)
                    break

            end_time = time.time()
            logger.info(f"Download completed in {end_time - start_time:.2f} seconds.")

            if progress_callback:
                progress_callback("Downloaded")
            return metadata
    except Exception as e:
        logger.error(f"An error occurred while downloading: {e}")
        if progress_callback:
            progress_callback("Failed")
        raise
