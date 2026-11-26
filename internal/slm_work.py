import json
import re
import inspect
import requests
from internal.logger import get_logger

logger = get_logger(__name__)
from internal.settings import get_settings
from internal.metadata_struct import Metadata_SLM


class SLM_work:
    SYSTEM_INSTRUCTION = (
        "You are a strict music metadata extractor. Output ONLY one valid JSON object and nothing else.\n"
        "Schema: "
        '{"artists": [str], "title": str, "album": str|null, "album_artist": str|null, '
        '"genre": str|null, "remix": str, "remixer": str|null, "year": int|null, "is_ambiguous": bool}.\n'
        "Rules:\n"
        "1. artists: array of individual artist names; split feat./ft./with/&/x/, into separate items. Never put the track title in artists.\n"
        "2. uploader vs artist vs remixer: YouTube uploaders are often reuploaders, lyric channels, or labels—ignore them unless they are the real artist. If they remixed the track, put the remix label/remixer in remix/remixer.\n"
        "3. noise removal: strip M/V, MV, Official Video/Audio, Lyric Video, Lyrics, Visualizer, HD, 4K, 60fps, Explicit, Clean, Eng Sub, Full Ver., OST/Soundtrack wrappers, and outer brackets/quotes.\n"
        "4. remix: short remix/version label (e.g. 'Alan Walker Remix', 'Radio Edit', 'Nightcore') without release years; empty string if none.\n"
        "5. year: 4-digit release year integer or null (never resolutions, bitrates, or part numbers).\n"
        "6. Prefer SearXNG web context when provided to verify original artist, title, album, album_artist, genre, and release year. Never invent facts; use null if unknown."
    )

    def __init__(self, settings: dict = None) -> None:
        self.settings = settings if settings else get_settings()
        slm_cfg = self.settings.get("slm", {})

        self.base_url: str = str(slm_cfg.get("base_url", "http://localhost:11434")).rstrip("/")
        self.model_name: str = str(slm_cfg.get("model", "phi4-mini"))
        self.keep_alive: str = str(slm_cfg.get("keep_alive", "5m"))
        self.timeout: int = int(slm_cfg.get("timeout", 60))

        self.is_ready: bool = False

        try:
            self.check_ollama()
            self.is_ready = True
        except Exception as e:
            logger.warning(f"Ollama is not ready. {e}")

    def check_ollama(self) -> bool:
        """
        Check if Ollama HTTP server is reachable and if the configured model is installed.
        Raises Exception if Ollama is unreachable or model is missing.
        """
        PIPELINE = f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"
        model_name = self.model_name

        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise Exception(f"Ollama server is not reachable at {self.base_url}: {e}")

        models = data.get("models", []) if isinstance(data, dict) else []
        installed_names = [
            str(m.get("model") or m.get("name") or "")
            for m in models
            if isinstance(m, dict)
        ]

        for name in installed_names:
            if model_name == name or model_name == name.split(":")[0]:
                logger.info(f"Model {model_name} is ready at {self.base_url}.")
                return True

        model_list_str = ", ".join(installed_names) if installed_names else "none"
        raise Exception(f"Model {model_name} is not installed. Installed models: {model_list_str}.")

    def _calculate_confidence(self, json_output: dict) -> float:
        if json_output.get("is_ambiguous") is True:
            return 0.2

        score = 1.0
        artists = json_output.get("artists") or json_output.get("artist") or []
        title = json_output.get("title") or json_output.get("song_name") or ""

        if not artists:
            score -= 0.35
        if not title:
            score -= 0.35

        return round(max(score, 0.0), 2)

    @staticmethod
    def _extract_json_dict(raw_content: str) -> dict:
        cleaned = raw_content.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed

        raise ValueError("Model output did not contain a valid JSON object.")

    _NOISE_CORE_PATTERN = (
        r"(?:"
        r"official\s+(?:music\s+)?(?:video|audio|lyric(?:s)?\s+video|visualizer|mv|m/v|hd\s+video)"
        r"|music\s+video"
        r"|lyric(?:s)?\s+video"
        r"|color\s+coded(?:\s+lyrics)?"
        r"|han\s*/\s*rom\s*/\s*eng"
        r"|eng(?:lish)?\s+sub(?:s|titles)?"
        r"|performance\s+video"
        r"|dance\s+practice(?:\s+video)?"
        r"|special\s+clip"
        r"|m\s*/\s*v"
        r"|m\.v\.?"
        r"|mv"
        r"|visualizer"
        r"|lyrics?"
        r"|audio(?:\s+only)?"
        r"|explicit"
        r"|clean\s+version"
        r"|full\s+ver(?:sion)?\.?"
        r"|hq|hd|uhd|4k|8k|1080p|720p|60fps|320kbps"
        r")"
    )

    _BRACKETED_NOISE_RE = re.compile(
        r"[\(\[\{【「『]\s*" + _NOISE_CORE_PATTERN + r"(?:\s*[\|/\-•]\s*" + _NOISE_CORE_PATTERN + r")*\s*[\)\]\}】」』]",
        flags=re.IGNORECASE,
    )
    _TRAILING_NOISE_RE = re.compile(
        r"(?:\s*[\|\-–—/:]\s*|\s+)" + _NOISE_CORE_PATTERN + r"\s*$",
        flags=re.IGNORECASE,
    )
    _LEADING_NOISE_RE = re.compile(
        r"^\s*" + _NOISE_CORE_PATTERN + r"(?:\s*[\|\-–—/:]\s*|\s+)",
        flags=re.IGNORECASE,
    )
    _EXACT_NOISE_RE = re.compile(
        r"^\s*" + _NOISE_CORE_PATTERN + r"\s*$",
        flags=re.IGNORECASE,
    )

    @classmethod
    def _strip_video_noise(cls, text: str | None) -> str:
        if not text:
            return ""
        cleaned = str(text)
        prev = None
        while cleaned != prev:
            prev = cleaned
            cleaned = cls._BRACKETED_NOISE_RE.sub(" ", cleaned)
            cleaned = cls._TRAILING_NOISE_RE.sub("", cleaned)
            cleaned = cls._LEADING_NOISE_RE.sub("", cleaned)
            cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" \t\r\n-|/:")
        if cls._EXACT_NOISE_RE.match(cleaned):
            return ""
        return cleaned

    @staticmethod
    def _clean_str(value) -> str | None:
        if value is None:
            return None
        s = str(value).strip()
        if not s or s.lower() in ("null", "none", "unknown", "n/a"):
            return None
        return s

    @staticmethod
    def _clean_artists(value) -> list[str]:
        if not value:
            return []
        if isinstance(value, str):
            val = value.strip()
            return [val] if val else []
        if isinstance(value, list):
            result = []
            for item in value:
                s = str(item).strip()
                if s and s.lower() not in ("null", "none", "unknown", "n/a"):
                    result.append(s)
            return result
        return []

    @staticmethod
    def _clean_year(value) -> int | None:
        if value is None or isinstance(value, bool):
            return None
        match = re.search(r"\b(19\d{2}|20\d{2})\b", str(value))
        if match:
            return int(match.group(1))
        return None

    def get_clean_metadata(
        self,
        dirty_title: str,
        search_context: str = "",
        missing_fields: list[str] = None,
        uploader: str = "",
    ) -> Metadata_SLM:
        PIPELINE = f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"

        if not self.is_ready:
            try:
                self.check_ollama()
                self.is_ready = True
            except Exception as e:
                raise Exception(f"Ollama is not ready. {e}")

        sanitized_title = self._strip_video_noise(dirty_title) or dirty_title
        prompt_parts = [f"Video Title: {sanitized_title}"]
        if uploader:
            prompt_parts.append(f"YouTube Uploader: {uploader}")
        if missing_fields:
            prompt_parts.append(f"Missing fields to fill: {', '.join(missing_fields)}")
        if search_context:
            prompt_parts.append(f"SearXNG Context:\n{search_context}")
        prompt_parts.append("Extract clean music metadata JSON now.")
        full_prompt = "\n\n".join(prompt_parts)

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": self.SYSTEM_INSTRUCTION},
                {"role": "user", "content": full_prompt},
            ],
            "stream": False,
            "keep_alive": self.keep_alive,
            "format": "json",
            "options": {
                "temperature": 0.0,
                "num_predict": 320,
            },
        }

        raw_content = ""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            raw_content = str(data.get("message", {}).get("content", ""))

            parsed = self._extract_json_dict(raw_content)
            output = Metadata_SLM()
            raw_title = self._clean_str(parsed.get("title") or parsed.get("song_name"))
            output.song_name = self._clean_str(self._strip_video_noise(raw_title)) if raw_title else None

            raw_artists = self._clean_artists(parsed.get("artists") or parsed.get("artist"))
            output.artist = [
                cleaned_a
                for a in raw_artists
                if (cleaned_a := self._clean_str(self._strip_video_noise(a)))
            ]

            output.album = self._clean_str(parsed.get("album"))
            output.album_artist = self._clean_str(parsed.get("album_artist"))
            output.genre = self._clean_str(parsed.get("genre"))

            remix_val = self._clean_str(parsed.get("remix"))
            remixer_val = self._clean_str(parsed.get("remixer"))
            raw_remix = remix_val or remixer_val
            output.remix = self._clean_str(self._strip_video_noise(raw_remix)) if raw_remix else None

            output.year = self._clean_year(parsed.get("year"))
            output.confidence = self._calculate_confidence(parsed)
            return output
        except Exception as e:
            logger.error(f"Failed to parse text from Ollama: {e}")
            logger.error(f"    Input: {dirty_title}")
            logger.error(f"    Output: {raw_content}")
            raise
