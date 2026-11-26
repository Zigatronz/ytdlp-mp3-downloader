import logging
from pathlib import Path

LOG_PATH = Path("app.log")
DEFAULT_MAX_LOG_LINES = 1000
_CONFIGURED = False
_FIFO_HANDLER: "FIFOLineFileHandler | None" = None


class FIFOLineFileHandler(logging.Handler):
    """
    File handler that appends formatted log lines to app.log and enforces a
    FIFO maximum line count (dropping oldest lines first when exceeded).
    """

    def __init__(self, filepath: Path = LOG_PATH, max_lines: int = DEFAULT_MAX_LOG_LINES) -> None:
        super().__init__()
        self.filepath = Path(filepath)
        self.max_lines = max(1, int(max_lines))

    def set_max_lines(self, max_lines: int) -> None:
        self.acquire()
        try:
            self.max_lines = max(1, int(max_lines))
            self._trim_if_needed()
        finally:
            self.release()

    def _trim_if_needed(self) -> None:
        if not self.filepath.exists():
            return
        try:
            lines = self.filepath.read_text(encoding="utf-8", errors="replace").splitlines()
            if len(lines) > self.max_lines:
                trimmed = lines[-self.max_lines :]
                self.filepath.write_text("\n".join(trimmed) + "\n", encoding="utf-8")
        except Exception:
            pass

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.acquire()
            try:
                lines: list[str] = []
                if self.filepath.exists():
                    lines = self.filepath.read_text(encoding="utf-8", errors="replace").splitlines()
                lines.extend(msg.splitlines() or [""])
                if len(lines) > self.max_lines:
                    lines = lines[-self.max_lines :]
                self.filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")
            finally:
                self.release()
        except Exception:
            self.handleError(record)


def configure_logging(max_lines: int = DEFAULT_MAX_LOG_LINES) -> None:
    global _CONFIGURED, _FIFO_HANDLER

    root_logger = logging.getLogger("ytdlp_mp3")
    root_logger.setLevel(logging.INFO)
    root_logger.propagate = False

    if not _CONFIGURED:
        formatter = logging.Formatter(
            fmt="[ %(asctime)s ] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)

        _FIFO_HANDLER = FIFOLineFileHandler(LOG_PATH, max_lines=max_lines)
        _FIFO_HANDLER.setLevel(logging.INFO)
        _FIFO_HANDLER.setFormatter(formatter)

        root_logger.addHandler(console_handler)
        root_logger.addHandler(_FIFO_HANDLER)
        _CONFIGURED = True
    elif _FIFO_HANDLER is not None:
        _FIFO_HANDLER.set_max_lines(max_lines)


def get_logger(name: str) -> logging.Logger:
    if not _CONFIGURED:
        configure_logging(DEFAULT_MAX_LOG_LINES)
    short_name = name.removeprefix("internal.")
    return logging.getLogger(f"ytdlp_mp3.{short_name}")
