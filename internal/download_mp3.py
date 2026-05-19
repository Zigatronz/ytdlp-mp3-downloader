import yt_dlp
from typing import Dict, Tuple
import browser_cookie3

def download_mp3(url: str, output_folder: str = ".") -> Tuple[str, Dict[str, str]]:
    browser_functions = [
        ('Firefox', browser_cookie3.firefox),
        ('Edge', browser_cookie3.edge),
        ('Brave', browser_cookie3.brave),
        ('Opera', browser_cookie3.opera),
        ('Chrome', browser_cookie3.chrome),  # Kept last due to App-Bound Encryption locks
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

        except Exception:
            # Skip any browser that fails to provide cookies, as some may have App-Bound Encryption or other issues
            continue

    cj = combined_jar

    ydl_params = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_folder}/%(uploader)s - %(title)s.%(ext)s',
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
                'already_have_thumbnail': False,
            }
        ],
        'cookiejar': cj,
        'quiet': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_params) as ydl:
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

            return final_path, metadata
    except Exception as e:
        print(f"An error occurred while downloading: {e}")
        raise
