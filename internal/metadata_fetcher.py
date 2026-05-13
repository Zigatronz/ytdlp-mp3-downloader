
import requests
import music_tag

class metadata_fetcher:
    def __init__(self, song_title):
        self.song_title = song_title

        self.mp3_path = None
        self.url = None

        self.metadata = {
            "title": None,
            "artist": None,
            "album": None,
            "album_artist": None,
            "year": None,
            "genre": None,
            "comment": None,
            "artwork_url": None
        }

    def fetch(self):
        url = "https://itunes.apple.com/search"
        parameters = {
            "term": self.song_title,
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
                self.metadata["title"] = track.get("trackName")
                self.metadata["artist"] = track.get("artistName")
                self.metadata["album"] = track.get("collectionName")
                self.metadata["album_artist"] = track.get("artistName")
                self.metadata["year"] = track.get("releaseDate", "")[:4]  # Extract year from release date
                self.metadata["genre"] = track.get("primaryGenreName")
                self.metadata["artwork_url"] = track.get("artworkUrl100")
                return self.metadata
            else:
                raise ValueError("No matching track found.")

        except Exception as e:
            print(f"An error occurred while fetching metadata: {e}")
            raise

    def apply_metadata(self, mp3_path):
        self.mp3_path = mp3_path

        def download_cover_art(url):
            try:
                response = requests.get(url)
                response.raise_for_status()
                return response.content
            except Exception as e:
                print(f"An error occurred while downloading cover art: {e}")
                return None

        try:
            audio_file : music_tag.AudioFile = music_tag.load_file(mp3_path)
            if self.metadata.get("title"):
                audio_file["title"] = self.metadata.get("title")
            else:
                audio_file["title"] = self.song_title
            if self.metadata.get("artist"):
                audio_file["artist"] = self.metadata.get("artist")
            if self.metadata.get("album"):
                audio_file["album"] = self.metadata.get("album")
            if self.metadata.get("album_artist"):
                audio_file["albumartist"] = self.metadata.get("album_artist")
            if self.metadata.get("year"):
                audio_file["year"] = self.metadata.get("year")
            if self.metadata.get("genre"):
                audio_file["genre"] = self.metadata.get("genre")
            if self.metadata.get("comment"):
                audio_file["comment"] = self.metadata.get("comment")
            cover_art_url = self.metadata.get("artwork_url")
            if cover_art_url:
                cover_art_data = download_cover_art(cover_art_url)
                if cover_art_data:
                    audio_file["artwork"] = cover_art_data
                else:
                    print("Cover art could not be downloaded, skipping embedding.")
            else:
                print("No cover art URL found, skipping embedding.")
            audio_file.save()
        except Exception as e:
            print(f"An error occurred while applying metadata: {e}")
            raise
