import io
import copy
import requests
import music_tag
from datetime import datetime
from PIL import Image, UnidentifiedImageError
from internal.logger import get_logger

logger = get_logger(__name__)
from pathlib import Path
import inspect


class Metadata_MP3:
    CORE_TEXT_FIELDS = ("song_title", "artist", "album", "album_artist", "year", "genre")

    def __init__(self):
        """
        Represents and manages MP3 metadata, cached artwork bytes, and runtime-only field provenance.
        """
        # --- Core Tags ---
        self.song_title: str | None = None
        self.artist: str | None = None
        self.album: str | None = None
        self.album_artist: str | None = None
        self.year: int | None = None
        self.genre: str | None = None
        self.remix: str | None = None
        self.comment: list[str] = []

        # --- Library Organization Tags ---
        self.track_number: int | None = None
        self.total_tracks: int | None = None
        self.disc_number: int | None = None
        self.total_discs: int | None = None
        self.composer: str | None = None

        # --- Advanced & ID Tags ---
        self.isrc: str | None = None
        self.lyrics: str | None = None

        # --- Artwork ---
        self.artwork_url: str | None = None
        self.artwork_bytes: bytes | None = None

        # --- Local ---
        self.mp3_path: str | None = None

        # --- Session/Runtime-only field provenance (not persisted to disk/JSON) ---
        self.field_sources: dict[str, str] = {}

    def set_field(self, field: str, value, source: str, overwrite: bool = False) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return False

        current = getattr(self, field, None)
        is_empty = current is None or (isinstance(current, str) and not current.strip())
        if overwrite or is_empty:
            setattr(self, field, value)
            if source:
                self.field_sources[field] = source
            return True
        return False

    def has_artwork(self) -> bool:
        if self.artwork_bytes:
            return True
        if not self.artwork_url or not str(self.artwork_url).strip():
            return False
        art = str(self.artwork_url).strip()
        if art.startswith("http://") or art.startswith("https://"):
            return True
        return Path(art).is_file()

    def get_missing_core_tags(self, include_artwork: bool = False) -> list[str]:
        missing = []
        for field in self.CORE_TEXT_FIELDS:
            val = getattr(self, field, None)
            if val is None or (isinstance(val, str) and not val.strip()):
                missing.append(field)
        if include_artwork and not self.has_artwork():
            missing.append("artwork_url")
        return missing

    def has_all_core_tags(self, include_artwork: bool = False) -> bool:
        return len(self.get_missing_core_tags(include_artwork=include_artwork)) == 0

    def clone(self) -> "Metadata_MP3":
        cloned = Metadata_MP3()
        cloned.song_title = self.song_title
        cloned.artist = self.artist
        cloned.album = self.album
        cloned.album_artist = self.album_artist
        cloned.year = self.year
        cloned.genre = self.genre
        cloned.remix = self.remix
        cloned.comment = list(self.comment)
        cloned.track_number = self.track_number
        cloned.total_tracks = self.total_tracks
        cloned.disc_number = self.disc_number
        cloned.total_discs = self.total_discs
        cloned.composer = self.composer
        cloned.isrc = self.isrc
        cloned.lyrics = self.lyrics
        cloned.artwork_url = self.artwork_url
        cloned.artwork_bytes = bytes(self.artwork_bytes) if self.artwork_bytes else None
        cloned.mp3_path = self.mp3_path
        cloned.field_sources = copy.deepcopy(self.field_sources)
        return cloned

    def __str__(self) -> str:
        out_dict = {
            "song_title": self.song_title,
            "artist": self.artist,
            "album": self.album,
            "album_artist": self.album_artist,
            "year": self.year,
            "genre": self.genre,
            "remix": self.remix,
            "comment": self.comment,
            "track_number": self.track_number,
            "total_tracks": self.total_tracks,
            "disc_number": self.disc_number,
            "total_discs": self.total_discs,
            "composer": self.composer,
            "isrc": self.isrc,
            "lyrics": self.lyrics,
            "artwork_url": self.artwork_url,
            "has_artwork_bytes": bool(self.artwork_bytes),
            "mp3_path": self.mp3_path,
            "field_sources": self.field_sources,
        }
        return str(out_dict)

    @staticmethod
    def convert_image_bytes_to_jpeg(raw_bytes: bytes) -> bytes:
        image_data = io.BytesIO(raw_bytes)
        image_data.seek(0)
        with Image.open(image_data) as img:
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")
            output_bytes = io.BytesIO()
            img.save(output_bytes, format="JPEG", quality=90)
            return output_bytes.getvalue()

    def _get_artwork(self, url: str) -> bytes:
        """
        Loads an image from a URL or local path and converts it to standard JPEG bytes.
        """
        PIPELINE = f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"

        try:
            if url.startswith("http://") or url.startswith("https://"):
                response = requests.get(
                    url,
                    timeout=10,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "")
                data = response.content
                if content_type and not content_type.startswith("image/"):
                    logger.warning(f"Artwork URL returned non-image Content-Type: {content_type}")
            else:
                with open(url, "rb") as fh:
                    data = fh.read()

            try:
                return self.convert_image_bytes_to_jpeg(data)
            except UnidentifiedImageError:
                sample = data[:128] if isinstance(data, (bytes, bytearray)) else b""
                logger.warning(f"Downloaded data could not be identified as an image. First bytes: {sample!r}")
                raise
        except Exception as e:
            logger.error(f"Error processing artwork from URL/local path: {e}")
            raise

    def preload_artwork_bytes(self) -> bytes | None:
        if self.artwork_bytes:
            return self.artwork_bytes
        if not self.artwork_url:
            return None
        try:
            self.artwork_bytes = self._get_artwork(self.artwork_url)
            return self.artwork_bytes
        except Exception:
            return None

    def embed_metadata(self, file_path: Path | str, clear_empty: bool = False) -> None:
        """
        Embeds metadata into an MP3 file using music_tag.
        When clear_empty=True, empty core text fields are explicitly cleared in the file tags.
        """
        PIPELINE = f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"

        try:
            f = music_tag.load_file(str(file_path))

            if self.song_title:
                f["tracktitle"] = self.song_title
            elif clear_empty:
                f.remove_tag("tracktitle")

            if self.artist:
                f["artist"] = self.artist
            elif clear_empty:
                f.remove_tag("artist")

            if self.album:
                f["album"] = self.album
            elif clear_empty:
                f.remove_tag("album")

            if self.album_artist:
                f["albumartist"] = self.album_artist
            elif clear_empty:
                f.remove_tag("albumartist")

            if self.year:
                f["year"] = int(self.year)
            elif clear_empty:
                f.remove_tag("year")

            if self.genre:
                f["genre"] = self.genre
            elif clear_empty:
                f.remove_tag("genre")

            comment_items = [c.strip() for c in self.comment if c and c.strip()]
            if comment_items:
                f["comment"] = "\n".join(comment_items)
            elif clear_empty:
                f.remove_tag("comment")

            if self.track_number:
                f["tracknumber"] = int(self.track_number)
            if self.total_tracks:
                f["totaltracks"] = int(self.total_tracks)
            if self.disc_number:
                f["discnumber"] = int(self.disc_number)
            if self.total_discs:
                f["totaldiscs"] = int(self.total_discs)
            if self.composer:
                f["composer"] = self.composer
            if self.isrc:
                f["isrc"] = self.isrc
            if self.lyrics:
                f["lyrics"] = self.lyrics

            if self.artwork_bytes:
                try:
                    f["artwork"] = self.artwork_bytes
                except Exception as e:
                    logger.warning(f"Unable to set cached artwork for {file_path}. Error: {e}")
            elif self.artwork_url:
                try:
                    self.artwork_bytes = self._get_artwork(self.artwork_url)
                    f["artwork"] = self.artwork_bytes
                except Exception as e:
                    logger.warning(f"Unable to set artwork for {file_path}. Error: {e}")

            f.save()
        except Exception as e:
            logger.error(f"Error saving metadata to file: {e}")
            raise


class Metadata_ITunes:
    def __init__(self):
        self.trackName: str | None = None
        self.artistName: str | None = None
        self.collectionName: str | None = None
        self.releaseDate: datetime | None = None
        self.primaryGenreName: str | None = None
        self.artworkUrl100: str | None = None

    def __str__(self) -> str:
        out_dict = {
            "trackName": self.trackName,
            "artistName": self.artistName,
            "collectionName": self.collectionName,
            "releaseDate": self.releaseDate,
            "primaryGenreName": self.primaryGenreName,
            "artworkUrl100": self.artworkUrl100,
        }
        return str(out_dict)

    def merge_to_mp3_metadata(
        self,
        mp3_metadata: Metadata_MP3,
        overwrite: bool = False,
        source_label: str = "iTunes",
    ) -> Metadata_MP3:
        """
        Merges iTunes metadata into an MP3 metadata object, filling only missing fields unless overwrite=True.
        """
        mp3_metadata.set_field("song_title", self.trackName, source_label, overwrite=overwrite)
        mp3_metadata.set_field("artist", self.artistName, source_label, overwrite=overwrite)
        mp3_metadata.set_field("album", self.collectionName, source_label, overwrite=overwrite)
        mp3_metadata.set_field("album_artist", self.artistName, source_label, overwrite=overwrite)
        if self.releaseDate:
            mp3_metadata.set_field("year", int(self.releaseDate.year), source_label, overwrite=overwrite)
        mp3_metadata.set_field("genre", self.primaryGenreName, source_label, overwrite=overwrite)
        if self.artworkUrl100 and (overwrite or not mp3_metadata.has_artwork()):
            mp3_metadata.artwork_url = self.artworkUrl100
            mp3_metadata.artwork_bytes = None
            mp3_metadata.field_sources["artwork_url"] = source_label
        return mp3_metadata


class Metadata_YouTube:
    def __init__(self):
        self.title: str | None = None
        self.track: str | None = None
        self.uploader: str | None = None
        self.artist: str | None = None
        self.album: str | None = None
        self.album_artist: str | None = None
        self.genre: str | None = None
        self.release_year: int | None = None
        self.creators: list[str] | None = None
        self.description: str | None = None
        self.id: str | None = None
        self.duration: int | None = None
        self.view_count: int | None = None
        self.upload_date: datetime | None = None
        self.url: str | None = None
        self.artwork_url: str | None = None
        self.file_path: str | None = None

    def __str__(self) -> str:
        out_dict = {
            "title": self.title,
            "track": self.track,
            "uploader": self.uploader,
            "artist": self.artist,
            "album": self.album,
            "album_artist": self.album_artist,
            "genre": self.genre,
            "release_year": self.release_year,
            "creators": self.creators,
            "description": self.description,
            "id": self.id,
            "duration": self.duration,
            "view_count": self.view_count,
            "upload_date": self.upload_date,
            "url": self.url,
            "artwork_url": self.artwork_url,
            "file_path": self.file_path,
        }
        return str(out_dict)

    def get_artist(self) -> str:
        if self.artist:
            return self.artist
        elif self.creators:
            return ", ".join(self.creators) if len(self.creators) > 1 else self.creators[0]
        elif self.uploader:
            return self.uploader
        return ""

    def clean_up_local_thumbnail(self) -> None:
        if not self.artwork_url:
            return
        art = str(self.artwork_url)
        if art.startswith("http://") or art.startswith("https://"):
            return
        local_path = Path(art)
        if local_path.is_file():
            try:
                local_path.unlink()
            except Exception:
                pass

    def merge_to_mp3_metadata(
        self,
        mp3_metadata: Metadata_MP3,
        include_fallback_fields: bool = False,
        overwrite: bool = False,
        source_label: str = "YouTube",
    ) -> Metadata_MP3:
        """
        Merges YouTube metadata into an MP3 metadata object.
        When include_fallback_fields=False, only structured music tags (track/artist/album/release_year/genre)
        plus artwork/path/url are applied so channel reuploaders or messy video titles do not block
        SearXNG+SLM or iTunes from identifying the real artist, title, or remixer.
        """
        if self.track:
            mp3_metadata.set_field("song_title", self.track, source_label, overwrite=overwrite)
        elif include_fallback_fields and self.title:
            mp3_metadata.set_field("song_title", self.title, f"{source_label} (Fallback)", overwrite=overwrite)

        if self.artist:
            mp3_metadata.set_field("artist", self.artist, source_label, overwrite=overwrite)
        elif self.creators:
            creators_str = ", ".join(self.creators) if len(self.creators) > 1 else self.creators[0]
            mp3_metadata.set_field("artist", creators_str, source_label, overwrite=overwrite)
        elif include_fallback_fields and self.uploader:
            mp3_metadata.set_field("artist", self.uploader, f"{source_label} (Uploader)", overwrite=overwrite)

        if self.album:
            mp3_metadata.set_field("album", self.album, source_label, overwrite=overwrite)

        if self.album_artist:
            mp3_metadata.set_field("album_artist", self.album_artist, source_label, overwrite=overwrite)
        elif include_fallback_fields and mp3_metadata.artist:
            mp3_metadata.set_field("album_artist", mp3_metadata.artist, f"{source_label} (Fallback)", overwrite=overwrite)

        if self.release_year:
            try:
                mp3_metadata.set_field("year", int(self.release_year), source_label, overwrite=overwrite)
            except (TypeError, ValueError):
                pass
        elif include_fallback_fields and self.upload_date:
            mp3_metadata.set_field("year", int(self.upload_date.year), f"{source_label} (Upload Date)", overwrite=overwrite)

        if self.genre:
            mp3_metadata.set_field("genre", self.genre, source_label, overwrite=overwrite)

        if self.artwork_url and (overwrite or not mp3_metadata.has_artwork()):
            mp3_metadata.artwork_url = self.artwork_url
            mp3_metadata.field_sources["artwork_url"] = source_label
        if self.file_path and (overwrite or not mp3_metadata.mp3_path):
            mp3_metadata.mp3_path = self.file_path
        if self.url and self.url not in mp3_metadata.comment:
            mp3_metadata.comment.append(self.url)
            mp3_metadata.field_sources.setdefault("comment", source_label)
        return mp3_metadata


class Metadata_SLM:
    def __init__(self):
        self.song_name: str | None = None
        self.artist: list[str] | None = None
        self.album: str | None = None
        self.album_artist: str | None = None
        self.genre: str | None = None
        self.remix: str | None = None
        self.year: int | None = None
        self.confidence: float = 0.0

    def __str__(self) -> str:
        out_dict = {
            "song_name": self.song_name,
            "artist": self.artist,
            "album": self.album,
            "album_artist": self.album_artist,
            "genre": self.genre,
            "remix": self.remix,
            "year": self.year,
            "confidence": self.confidence,
        }
        return str(out_dict)

    def merge_to_mp3_metadata(
        self,
        mp3_metadata: Metadata_MP3,
        required_confidence: float = 0.5,
        overwrite: bool = False,
        source_label: str = "SearXNG + Ollama",
    ) -> Metadata_MP3:
        """
        Merges SLM metadata into an MP3 metadata object, filling only missing pieces unless overwrite=True.
        """
        if self.confidence is not None and self.confidence >= required_confidence:
            mp3_metadata.set_field("song_title", self.song_name, source_label, overwrite=overwrite)
            if self.artist:
                artist_str = ", ".join(self.artist) if len(self.artist) > 1 else self.artist[0]
                mp3_metadata.set_field("artist", artist_str, source_label, overwrite=overwrite)
                mp3_metadata.set_field(
                    "album_artist",
                    self.album_artist or artist_str,
                    source_label,
                    overwrite=overwrite,
                )
            elif self.album_artist:
                mp3_metadata.set_field("album_artist", self.album_artist, source_label, overwrite=overwrite)

            mp3_metadata.set_field("album", self.album, source_label, overwrite=overwrite)
            mp3_metadata.set_field("genre", self.genre, source_label, overwrite=overwrite)
            if self.year:
                try:
                    mp3_metadata.set_field("year", int(self.year), source_label, overwrite=overwrite)
                except (TypeError, ValueError):
                    pass
            if self.remix:
                mp3_metadata.set_field("remix", self.remix, source_label, overwrite=overwrite)
        return mp3_metadata
