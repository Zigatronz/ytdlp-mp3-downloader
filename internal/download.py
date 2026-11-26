from internal.ytdlp import ytdlp
from internal.itunes_metadata_fetcher import itunes_metadata_fetcher
from internal.metadata_struct import (
    Metadata_MP3,
    Metadata_YouTube,
    Metadata_ITunes,
    Metadata_SLM,
)
from internal.logger import get_logger

logger = get_logger(__name__)
from internal.settings import get_settings
from internal.slm_work import SLM_work
from internal.searxng import SearXNG
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import os
import re
import time
import inspect


def _sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]+', "", name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned or "Untitled"


YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
}


def normalize_youtube_url(raw_url: str) -> str:
    """
    Validates and normalizes YouTube / YouTube Music video URLs, including:
    - https://www.youtube.com/watch?v=xxxxxxxx (with or without extra query params)
    - https://youtube.com/watch?v=xxxxxxxx
    - https://m.youtube.com/watch?v=xxxxxxxx
    - https://music.youtube.com/watch?v=xxxxxxxx
    - https://youtu.be/xxxxxxxx
    - https://www.youtube.com/shorts/xxxxxxxx, /embed/xxxxxxxx, /live/xxxxxxxx
    """
    if not raw_url or not raw_url.strip():
        raise ValueError("URL is empty.")

    candidate = raw_url.strip()
    if not candidate.startswith(("http://", "https://")):
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or host not in YOUTUBE_HOSTS:
        raise ValueError("URL is invalid.")

    path = parsed.path or ""
    query = parse_qs(parsed.query)
    video_id = None

    if host in ("youtu.be", "www.youtu.be"):
        segments = [seg for seg in path.split("/") if seg]
        if segments:
            video_id = segments[0]
    else:
        if path == "/watch" or path.startswith("/watch/"):
            v_vals = query.get("v")
            if v_vals and v_vals[0].strip():
                video_id = v_vals[0].strip()
        else:
            segments = [seg for seg in path.split("/") if seg]
            if len(segments) >= 2 and segments[0] in ("shorts", "embed", "live", "v"):
                video_id = segments[1].strip()

    if not video_id or not re.fullmatch(r"[A-Za-z0-9_-]{6,}", video_id):
        raise ValueError("URL is invalid.")

    target_host = "music.youtube.com" if host == "music.youtube.com" else "www.youtube.com"
    return f"https://{target_host}/watch?v={video_id}"


def build_track_stem(artist: str | None, title: str | None, remix: str | None = None, fallback: str = "Untitled") -> str:
    artist_part = (artist or "").strip() or "Unknown Artist"
    title_part = (title or "").strip() or fallback
    stem = f"{artist_part} - {title_part}"
    remix_part = (remix or "").strip()
    if remix_part:
        stem += f" ({remix_part})"
    return _sanitize_filename(stem)


class download:
    def __init__(
        self,
        settings: dict | None = None,
        slm: SLM_work | None = None,
        searxng: SearXNG | None = None,
        progress_callback=None,
        metadata_callback=None,
    ) -> None:
        self.settings = settings if settings else get_settings()
        self.slm = slm if slm else SLM_work(settings=self.settings)
        self.searxng = searxng if searxng else SearXNG(settings=self.settings)
        self.progress_callback = progress_callback
        self.metadata_callback = metadata_callback
        self.download_folder: Path = Path.cwd() / self.settings["app"]["download_folder"]

    def _notify(self, message: str) -> None:
        if self.progress_callback:
            self.progress_callback(message)

    def _emit_metadata(self, metadata: Metadata_MP3) -> None:
        if self.metadata_callback:
            self.metadata_callback(metadata.clone())

    def download(self, url: str) -> Metadata_MP3:
        """
        Download MP3 from YouTube URL and complete metadata incrementally:
        1. YouTube itself (no AI)
        2. SearXNG + SLM (phi4-mini via Ollama, keep_alive 5m; distinguishes artist vs reuploader vs remixer)
        3. iTunes Search API (no AI)
        4. SearXNG image search if thumbnail is still absent
        Stops early as soon as all core tags are present.
        """
        PIPELINE = f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"

        url = normalize_youtube_url(url)

        # Step 1: Download audio + extract native YouTube metadata (no AI)
        try:
            os.makedirs(self.download_folder, exist_ok=True)
            logger.info(f"Downloading from URL: {url}")
            metadata_yt = ytdlp(url, progress_callback=self.progress_callback)
            logger.info("Download completed successfully. " + Path(metadata_yt.file_path).stem)
        except Exception as e:
            self._notify("Failed")
            logger.error(f"An error occurred during download: {e}")
            raise

        metadata = Metadata_MP3()
        metadata_slm = Metadata_SLM()

        # Apply Step 1 (YouTube native structured tags first; raw uploader/title fallbacks reserved for after Steps 2-3)
        metadata_yt.merge_to_mp3_metadata(
            metadata,
            include_fallback_fields=False,
            overwrite=False,
            source_label="YouTube",
        )
        metadata.preload_artwork_bytes()
        self._emit_metadata(metadata)
        missing_after_yt = metadata.get_missing_core_tags(include_artwork=True)
        logger.info(f"Step 1 (YouTube) completed. Missing core tags: {missing_after_yt or 'None'}")

        # Step 2: SearXNG + SLM (Ollama phi4-mini, keep_alive 5m) - only if core text tags are still missing
        if not metadata.has_all_core_tags(include_artwork=False):
            missing_text_tags = metadata.get_missing_core_tags(include_artwork=False)
            slm_ready = bool(self.slm and self.slm.is_ready)
            searx_ready = bool(self.searxng and self.searxng.enabled and self.searxng.is_ready)

            if slm_ready:
                try:
                    self._notify("SearXNG + AI..." if searx_ready else "Running AI...")
                    logger.info(f"Step 2: Completing missing tags {missing_text_tags} via {'SearXNG + Ollama' if searx_ready else 'Ollama'}.")
                    start_time = time.time()

                    query_parts = []
                    if metadata.artist:
                        query_parts.append(metadata.artist)
                    if metadata.song_title:
                        query_parts.append(metadata.song_title)
                    search_query = " - ".join(query_parts) if query_parts else (metadata_yt.title or "")

                    searx_results = self.searxng.search_metadata(search_query) if searx_ready else []
                    search_context = self.searxng.format_context(searx_results) if searx_results else ""
                    slm_source = "SearXNG + Ollama" if searx_results else "Ollama"

                    slm_input = metadata_yt.title or search_query
                    metadata_slm = self.slm.get_clean_metadata(
                        slm_input,
                        search_context=search_context,
                        missing_fields=missing_text_tags,
                        uploader=metadata_yt.uploader or "",
                    )

                    if (not metadata_slm.artist or not metadata_slm.song_name) and metadata_yt.uploader:
                        alt_input = f"{metadata_yt.uploader} - {metadata_yt.title}"
                        if alt_input != slm_input:
                            alt_results = self.searxng.search_metadata(alt_input) if searx_ready else []
                            alt_context = self.searxng.format_context(alt_results) if alt_results else search_context
                            if alt_results:
                                slm_source = "SearXNG + Ollama"
                            metadata_slm_new = self.slm.get_clean_metadata(
                                alt_input,
                                search_context=alt_context,
                                missing_fields=missing_text_tags,
                                uploader=metadata_yt.uploader or "",
                            )
                            if metadata_slm_new.confidence > metadata_slm.confidence:
                                metadata_slm = metadata_slm_new

                    metadata_slm.merge_to_mp3_metadata(
                        metadata,
                        required_confidence=0.5,
                        overwrite=False,
                        source_label=slm_source,
                    )
                    self._emit_metadata(metadata)
                    end_time = time.time()
                    logger.info(f"Step 2 (SearXNG + SLM) took {end_time - start_time:.2f}s. "
                        f"Output: {metadata_slm}. "
                        f"Remaining missing: {metadata.get_missing_core_tags(include_artwork=True) or 'None'}")
                except Exception as e:
                    logger.error(f"An error occurred during Step 2 (SearXNG + SLM): {e}")
            else:
                logger.info("Skipping Step 2 (SearXNG + SLM) because Ollama is offline.")
        else:
            logger.info("All core text tags complete after Step 1 (YouTube). Skipping Step 2.")

        # Step 3: iTunes Search API (no AI) - only if any core tag or artwork is still missing
        if not metadata.has_all_core_tags(include_artwork=True):
            try:
                self._notify("Fetch iTunes...")
                logger.info("Step 3: Fetching missing metadata from iTunes.")
                start_time = time.time()

                itunes_queries: list[str] = []
                if metadata.artist and metadata.song_title:
                    itunes_queries.append(f"{metadata.artist} {metadata.song_title}")
                if metadata_yt.title and metadata_yt.title not in itunes_queries:
                    itunes_queries.append(metadata_yt.title)
                if metadata_yt.uploader and metadata_yt.title:
                    combo = f"{metadata_yt.uploader} {metadata_yt.title}"
                    if combo not in itunes_queries and metadata_yt.uploader.lower() not in metadata_yt.title.lower():
                        itunes_queries.append(combo)

                metadata_itunes = Metadata_ITunes()
                for query in itunes_queries:
                    if not query:
                        continue
                    try:
                        metadata_itunes = itunes_metadata_fetcher(query)
                        break
                    except Exception:
                        continue

                metadata_itunes.merge_to_mp3_metadata(metadata, overwrite=False, source_label="iTunes")
                metadata.preload_artwork_bytes()
                self._emit_metadata(metadata)
                end_time = time.time()
                logger.info(f"Step 3 (iTunes) took {end_time - start_time:.2f}s. "
                    f"Remaining missing: {metadata.get_missing_core_tags(include_artwork=True) or 'None'}")
            except Exception as e:
                logger.warning(f"An error occurred during iTunes metadata fetch: {e}")
        else:
            logger.info("All core tags and artwork complete before Step 3. Skipping iTunes.")

        # Apply YouTube raw fallbacks ONLY for basic fields still missing after Steps 1-3
        metadata_yt.merge_to_mp3_metadata(
            metadata,
            include_fallback_fields=True,
            overwrite=False,
            source_label="YouTube",
        )
        self._emit_metadata(metadata)

        # Step 4: If thumbnail/artwork is still absent, use SearXNG image search (only if SearXNG is online)
        if not metadata.has_artwork():
            if self.searxng and self.searxng.enabled and self.searxng.is_ready:
                self._notify("Fetch cover...")
                logger.info("Step 4: Thumbnail absent. Searching image via SearXNG.")
                thumb_query = " ".join(
                    p for p in [metadata.artist, metadata.song_title, metadata.album] if p
                ).strip() or (metadata_yt.title or "")
                found_thumb = self.searxng.search_thumbnail(thumb_query)
                if found_thumb:
                    metadata.artwork_url = found_thumb
                    metadata.artwork_bytes = None
                    metadata.field_sources["artwork_url"] = "SearXNG Image"
                    metadata.preload_artwork_bytes()
                    self._emit_metadata(metadata)
                    logger.info(f"Step 4: Found thumbnail URL via SearXNG: {found_thumb}")
                else:
                    logger.warning("Step 4: No thumbnail found via SearXNG image search.")
            else:
                logger.info("Step 4: Thumbnail absent, skipping SearXNG image search (offline/disabled).")
        else:
            logger.info("Thumbnail already present. Skipping Step 4 (SearXNG image search).")

        # Embed final metadata
        self._notify("Embedding...")
        logger.info(f"Embedding metadata: {metadata}")
        try:
            metadata.embed_metadata(metadata.mp3_path)
        except Exception as e:
            logger.error(f"An error occurred during embedding metadata: {e}")

        # Rename MP3 file cleanly: "<artist> - <title> (<remixer>).mp3"
        try:
            new_stem = build_track_stem(
                artist=metadata.artist or metadata_yt.get_artist(),
                title=metadata.song_title or metadata_yt.title,
                remix=metadata.remix or metadata_slm.remix,
                fallback=Path(metadata.mp3_path).stem,
            )
            new_music_path = self.download_folder / f"{new_stem}.mp3"

            current_path = Path(metadata.mp3_path)
            if current_path.resolve() != new_music_path.resolve():
                if new_music_path.exists():
                    counter = 2
                    while (self.download_folder / f"{new_stem} ({counter}).mp3").exists():
                        counter += 1
                    new_music_path = self.download_folder / f"{new_stem} ({counter}).mp3"
                os.rename(current_path, new_music_path)
                metadata.mp3_path = str(new_music_path)
            else:
                metadata.mp3_path = str(current_path)

            logger.info(f"Filename cleaned: {Path(metadata.mp3_path).stem}")
        except Exception as e:
            logger.error(f"An error occurred during filename cleaning: {e}")

        # Clean up local downloaded thumbnail file (artwork_bytes stays cached for GUI preview/re-editing)
        metadata_yt.clean_up_local_thumbnail()

        self._emit_metadata(metadata)
        self._notify("Done")
        logger.info("Download completed successfully. " + str(Path(metadata.mp3_path).absolute()))
        return metadata

