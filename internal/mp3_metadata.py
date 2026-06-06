import os, io
import requests
import music_tag
from PIL import Image
from internal.log_time import logTime

class Mp3Metadata:
    def __init__(self):
        """
        A comprehensive class to represent and manage MP3 metadata, including core tags,
        library organization tags, advanced identifiers, and artwork handling.
        """
        # --- Core Tags ---
        self.song_title: str = None
        self.artist: str = None
        self.album: str = None
        self.album_artist: str = None
        self.year: int = None
        self.genre: str = None
        self.comment: str = None
        
        # --- Library Organization Tags ---
        self.track_number: int = None
        self.total_tracks: int = None
        self.disc_number: int = None
        self.total_discs: int = None
        self.composer: str = None
        
        # --- Advanced & ID Tags ---
        self.isrc: str = None
        self.lyrics: str = None
        
        # --- Storage for Raw Artwork Data ---
        self.artwork_bytes: bytes = None

        # for json output reference
        self.artwork_url: str = None

        # extra fields for YouTube metadata
        self.file_path: str = None
        self.yt_v_id: str = None
        self.duration: int = None
        self.view_count: int = None
        self.yt_uploader: str = None
        self.yt_upload_date: str = None
        self.yt_webpage_url: str = None

    def to_json_friendly(self):
        """
        Converts the metadata object into a dictionary format that can be easily serialized to JSON.
        """
        return {
            "song_title": self.song_title,
            "artist": self.artist,
            "album": self.album,
            "album_artist": self.album_artist,
            "year": self.year,
            "genre": self.genre,
            "comment": self.comment,

            "track_number": self.track_number,
            "total_tracks": self.total_tracks,
            "disc_number": self.disc_number,
            "total_discs": self.total_discs,
            "composer": self.composer,

            "isrc": self.isrc,
            "lyrics": self.lyrics,

            "artwork_url": self.artwork_url,

            "file_path": self.file_path,
            "yt_v_id": self.yt_v_id,
            "duration": self.duration,
            "view_count": self.view_count,
            "yt_uploader": self.yt_uploader,
            "yt_upload_date": self.yt_upload_date,
            "yt_webpage_url": self.yt_webpage_url
        }

    def set_artwork_from_file(self, file_path: str, delete_original: bool = False):
        """
        Loads an image from a local file, converts it to standard JPEG bytes 
        (safely handling WebP, PNG, etc.), and stores it.
        """
        try:
            with Image.open(file_path) as img:
                # Convert WebP/PNG transparency (RGBA) to standard RGB for JPEG
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")
                
                image_data = io.BytesIO()
                img.save(image_data, format="JPEG", quality=90)
                
                self.artwork_bytes = image_data.getvalue()
                
            self.artwork_url = None  # Clear URL since we're using local file

            if delete_original:
                os.remove(file_path)
            
        except Exception as e:
            logTime(f"Error processing artwork from file: {e}", level="ERR")
            self.artwork_bytes = None
            raise

    def set_artwork_from_url(self, url: str):
        """
        Downloads an image from a URL, converts it to standard JPEG bytes 
        (safely handling WebP, PNG, etc.), and stores it.
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            image_data = io.BytesIO(response.content)
            with Image.open(image_data) as img:
                # Convert WebP/PNG transparency (RGBA) to standard RGB for JPEG
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")
                
                output_bytes = io.BytesIO()
                img.save(output_bytes, format="JPEG", quality=90)
                
                self.artwork_bytes = output_bytes.getvalue()
                
            self.artwork_url = url
                
        except Exception as e:
            logTime(f"Error processing artwork from URL: {e}", level="ERR")
            self.artwork_bytes = None
            raise

    def fill_holes_from(self, other):
        if isinstance(other, Mp3Metadata):
            for field in self.__dict__.keys():
                if getattr(self, field) is None and getattr(other, field) is not None:
                    setattr(self, field, getattr(other, field))
        else:
            logTime("fill_holes_from: Provided object is not of type Mp3Metadata but instead " + str(type(other)), level="ERR")
            raise TypeError("Expected an instance of Mp3Metadata not " + str(type(other)))

    def save_to_file(self, file_path: str):
        """
        Loads the target MP3 file using music-tag, maps all defined metadata
        fields to the file keys, and saves it to disk.
        """
        try:
            # Load the file wrapper
            f = music_tag.load_file(file_path)
            
            # Try to load artwork from URL if necessary
            if self.artwork_bytes is None and self.artwork_url is not None:
                try:
                    self.set_artwork_from_url(self.artwork_url)
                except Exception:
                    pass
            
            # Map core tags
            if self.song_title is not None: f['tracktitle'] = self.song_title
            if self.artist is not None: f['artist'] = self.artist
            if self.album is not None: f['album'] = self.album
            if self.album_artist is not None: f['albumartist'] = self.album_artist
            if self.year is not None: f['year'] = int(self.year)
            if self.genre is not None: f['genre'] = self.genre
            if self.comment is not None: f['comment'] = self.comment
            
            # Map library organization tags
            if self.track_number is not None: f['tracknumber'] = int(self.track_number)
            if self.total_tracks is not None: f['totaltracks'] = int(self.total_tracks)
            if self.disc_number is not None: f['discnumber'] = int(self.disc_number)
            if self.total_discs is not None: f['totaldiscs'] = int(self.total_discs)
            if self.composer is not None: f['composer'] = self.composer

            # Map advanced & ID tags
            if self.isrc is not None: f['isrc'] = self.isrc
            if self.lyrics is not None: f['lyrics'] = self.lyrics
            
            # Map processed artwork bytes
            if self.artwork_bytes is not None:
                f['artwork'] = self.artwork_bytes
                
            # Write changes directly back to the file
            f.save()
            
        except Exception as e:
            logTime(f"Error saving metadata to file: {e}", level="ERR")
            raise
