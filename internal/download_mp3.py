import yt_dlp
from typing import Dict, Tuple
import time, browser_cookie3, os
from internal.log_time import logTime

def scrape_youtube_cookies(output_txt_path: str = "youtube_cookies.txt") -> bool:
    """
    Extracts browser session cookies natively and writes them to a 
    standardized Netscape text format that yt-dlp strictly expects.
    """
    browser_functions = [
        ('Firefox', browser_cookie3.firefox),
        ('Edge', browser_cookie3.edge),
        ('Brave', browser_cookie3.brave),
        ('Opera', browser_cookie3.opera),
        ('Chrome', browser_cookie3.chrome),
    ]

    combined_jar = None
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
            logTime(f"Scraped active session tokens from: {name}", level="INF", print_this=True)
        except Exception:
            continue

    if combined_jar is None:
        return False

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

    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(cookie_file_content)

    return True


def download_mp3(url: str, output_folder: str = ".") -> Tuple[str, Dict[str, str]]:
    cookie_file = "youtube_cookies.txt"

    if os.path.exists(cookie_file):
        logTime("Existing cookie file found. Using it for authentication.", level="INF")
        has_cookies = True
    else:
        has_cookies = scrape_youtube_cookies(cookie_file)

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
        'quiet': False,
    }
    
    if has_cookies and os.path.exists(cookie_file):
        ydl_params['cookiejar'] = cookie_file
        
        # FIX: Force yt-dlp to use the standard desktop web player clients 
        # This prevents YouTube from serving DRM-protected TV/Mobile streams to your account.
        ydl_params['extractor_args'] = {
            'youtube': {
                'player_client': ['web', 'android'],
                'player_js_variant': ['web']
            }
        }
        
        # Mimic a standard Windows Firefox browser to align perfectly with your cookies
        ydl_params['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    else:
        logTime("No browser tokens generated. Defaulting to standard stream request.", level="WRN")

    try:
        with yt_dlp.YoutubeDL(ydl_params) as ydl:
            logTime(f"Starting download for URL: {url}", level="INF")
            info_dict = ydl.extract_info(url, download=True)
            requested_downloads = info_dict.get('requested_downloads', [])
            
            if requested_downloads:
                final_path = requested_downloads[-1].get('filepath')
            else:
                final_path = info_dict.get('_filename')

            upload_date = info_dict.get('upload_date')
            metadata = {
                "title": info_dict.get('title'),
                "uploader": info_dict.get('uploader'),
                "duration_seconds": info_dict.get('duration'),
                "view_count": info_dict.get('view_count'),
                "upload_date_day": upload_date[6:8],
                "upload_date_month": upload_date[4:6],
                "upload_date_year": upload_date[0:4],
                "description": info_dict.get('description'),
                "webpage_url": info_dict.get('webpage_url'),
                "thumbnail_url": info_dict.get('thumbnail')
            }

            # clean up .webp/.png/.jpg thumbnail if it exists
            webp_path = os.path.splitext(final_path)[0] + ".webp"
            png_path = os.path.splitext(final_path)[0] + ".png"
            jpg_path = os.path.splitext(final_path)[0] + ".jpg"

            for thumbnail_path in [webp_path, png_path, jpg_path]:
                if os.path.exists(thumbnail_path):
                    try:
                        os.remove(thumbnail_path)
                        logTime("Cleaned up temporary thumbnail file.", level="INF")
                    except Exception:
                        logTime("Failed to remove temporary thumbnail file.", level="WRN")

            return final_path, metadata
    except Exception as e:
        logTime(f"An error occurred while downloading: {e}", level="ERR")
        raise
