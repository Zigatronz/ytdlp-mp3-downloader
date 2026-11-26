import requests
from datetime import datetime
from internal.metadata_struct import Metadata_ITunes
from internal.logger import get_logger

logger = get_logger(__name__)
import inspect

def itunes_metadata_fetcher(song_title):
    """
    Fetches metadata for a given song title from the iTunes
    Search API and returns it as an Mp3Metadata object.
    """
    PIPELINE = inspect.currentframe().f_code.co_name

    url = "https://itunes.apple.com/search"
    parameters = {
        "term": song_title,
        "media": "music",
        "limit": 1
    }

    try:
        response = requests.get(url, params=parameters, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, dict):
            raise ValueError("Unexpected response format: expected a dictionary.")

        if data.get("resultCount", 0) > 0:
            track: dict = data["results"][0]
            metadata = Metadata_ITunes()
            metadata.trackName = track.get("trackName")
            metadata.artistName = track.get("artistName")
            metadata.collectionName = track.get("collectionName")
            release_date_raw = track.get("releaseDate")
            if release_date_raw:
                metadata.releaseDate = datetime.fromisoformat(release_date_raw.replace("Z", "+00:00"))
            metadata.primaryGenreName = track.get("primaryGenreName")
            artwork_url = track.get("artworkUrl100")
            if artwork_url:
                metadata.artworkUrl100 = artwork_url.replace("100x100bb", "600x600bb")

            return metadata
        else:
            raise ValueError("No matching track found.", song_title)

    except Exception as e:
        logger.error(f"An error occurred while fetching metadata: {e}")
        raise
