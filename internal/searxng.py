import io
import inspect
import requests
from PIL import Image
from internal.logger import get_logger

logger = get_logger(__name__)
from internal.settings import get_settings


class SearXNG:
    def __init__(self, settings: dict = None) -> None:
        self.settings = settings if settings else get_settings()
        cfg = self.settings.get("searxng", {})
        self.enabled: bool = bool(cfg.get("enabled", True))
        self.base_url: str = str(cfg.get("base_url", "http://localhost:8080")).rstrip("/")
        self.timeout: int = int(cfg.get("timeout", 10))
        self.max_results: int = int(cfg.get("max_results", 5))
        self.categories: str = str(cfg.get("categories", "general"))
        self.is_ready: bool = False

        if self.enabled:
            self.is_ready = self.check_available()

    def check_available(self) -> bool:
        PIPELINE = f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"
        if not self.enabled:
            return False

        try:
            response = requests.get(
                f"{self.base_url}/search",
                params={"q": "music", "format": "json"},
                timeout=min(self.timeout, 4),
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "results" in data:
                    logger.info(f"SearXNG is ready at {self.base_url}.")
                    return True
            logger.warning(f"SearXNG check returned HTTP {response.status_code} at {self.base_url}.")
            return False
        except Exception as e:
            logger.warning(f"SearXNG is not reachable at {self.base_url}: {e}")
            return False

    def search_metadata(self, query: str, max_results: int = None) -> list[dict]:
        """
        Queries SearXNG JSON API for factual music metadata context (artist, track, album, release year, genre).
        """
        PIPELINE = f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"
        if not self.enabled or not query or not query.strip():
            return []

        limit = max_results or self.max_results
        params = {
            "q": f"{query.strip()} song album genre release year",
            "format": "json",
            "categories": self.categories,
        }

        try:
            response = requests.get(
                f"{self.base_url}/search",
                params=params,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
            raw_results = payload.get("results", []) if isinstance(payload, dict) else []

            cleaned: list[dict] = []
            for item in raw_results[:limit]:
                if not isinstance(item, dict):
                    continue
                title = str(item.get("title") or "").strip()
                snippet = str(item.get("content") or "").strip()
                url = str(item.get("url") or "").strip()
                if title or snippet:
                    cleaned.append(
                        {
                            "title": title[:200],
                            "content": snippet[:350],
                            "url": url,
                        }
                    )

            self.is_ready = True
            logger.info(f"SearXNG returned {len(cleaned)} metadata results for query: {query}")
            return cleaned
        except Exception as e:
            logger.warning(f"SearXNG metadata search failed for '{query}': {e}")
            return []

    @staticmethod
    def format_context(results: list[dict]) -> str:
        if not results:
            return ""
        lines = []
        for idx, item in enumerate(results, start=1):
            title = item.get("title", "")
            content = item.get("content", "")
            url = item.get("url", "")
            lines.append(f"{idx}. {title} | {content} ({url})")
        return "\n".join(lines)

    def _validate_image_url(self, url: str) -> tuple[bool, int, int]:
        if not url or not (url.startswith("http://") or url.startswith("https://")):
            return False, 0, 0
        try:
            resp = requests.get(
                url,
                timeout=min(self.timeout, 8),
                headers={"User-Agent": "Mozilla/5.0"},
            )
            resp.raise_for_status()
            with Image.open(io.BytesIO(resp.content)) as img:
                width, height = img.size
                return True, width, height
        except Exception:
            return False, 0, 0

    def search_thumbnail(self, query: str, max_results: int = None) -> str | None:
        """
        Queries SearXNG image search to find a valid artwork/thumbnail URL when thumbnail is absent.
        """
        PIPELINE = f"{self.__class__.__name__}.{inspect.currentframe().f_code.co_name}"
        if not self.enabled or not query or not query.strip():
            return None

        limit = max_results or max(self.max_results, 8)
        params = {
            "q": f"{query.strip()} album cover",
            "format": "json",
            "categories": "images",
        }

        try:
            response = requests.get(
                f"{self.base_url}/search",
                params=params,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
            raw_results = payload.get("results", []) if isinstance(payload, dict) else []

            fallback_url = None
            for item in raw_results[:limit]:
                if not isinstance(item, dict):
                    continue
                for candidate_key in ("img_src", "thumbnail_src"):
                    candidate_url = str(item.get(candidate_key) or "").strip()
                    if not candidate_url:
                        continue
                    ok, width, height = self._validate_image_url(candidate_url)
                    if ok:
                        if width >= 200 and height >= 200:
                            logger.info(f"SearXNG image search selected thumbnail ({width}x{height}): {candidate_url}")
                            return candidate_url
                        if fallback_url is None:
                            fallback_url = candidate_url

            if fallback_url:
                logger.info(f"SearXNG image search selected fallback thumbnail: {fallback_url}")
            else:
                logger.warning(f"SearXNG image search found no valid thumbnail for: {query}")
            return fallback_url
        except Exception as e:
            logger.warning(f"SearXNG image search failed for '{query}': {e}")
            return None
