import requests
from internal.mp3_metadata import Mp3Metadata
from internal.log_time import logTime

def itunes_metadata_fetcher(song_title):
    """
    Fetches metadata for a given song title from the iTunes
    Search API and returns it as an Mp3Metadata object.
    """
    url = "https://itunes.apple.com/search"
    parameters = {
        "term": song_title,
        "media": "music",
        "limit": 1
    }

    try:
        response = requests.get(url, params=parameters)
        data = response.json()

        if not isinstance(data, dict):
            raise ValueError("Unexpected response format: expected a dictionary.")

        if data["resultCount"] > 0:
            track : dict = data["results"][0]
            metadata = Mp3Metadata()
            metadata.song_title = track.get("trackName")
            metadata.artist = track.get("artistName")
            metadata.album = track.get("collectionName")
            metadata.album_artist = track.get("artistName")
            metadata.year = track.get("releaseDate", "")[:4]  # Extract year from release date
            metadata.genre = track.get("primaryGenreName")
            metadata.artwork_url = track.get("artworkUrl100")
            return metadata
        else:
            raise ValueError("No matching track found.")

    except Exception as e:
        logTime(f"An error occurred while fetching metadata: {e}", level="ERR")
        raise


