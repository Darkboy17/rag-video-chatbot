import logging
from typing import Callable

ProgressCallback = Callable[[str], None]

logger = logging.getLogger("app.ingestion")
logger.setLevel(logging.INFO)


class IngestionProgress:
    """
    Reports ingestion progress to both backend logs and an optional caller.

    The streaming analyze endpoint passes a callback so the frontend can show
    the same messages that appear in the backend console.
    """

    def __init__(
        self,
        session_id: str,
        on_progress: ProgressCallback | None = None,
    ):
        self.session_id = session_id
        self.on_progress = on_progress

    def emit(self, message: str) -> None:
        logger.info("[session:%s] %s", self.session_id, message)

        if self.on_progress:
            self.on_progress(message)
