from dataclasses import dataclass, field
from typing import Dict, List

from langchain_core.messages import BaseMessage

from app.schemas.video import VideoMetadata


@dataclass
class SessionState:
    """
    In-memory session state.

    For production:
    - Store chat history in Redis/Postgres.
    - Store analyzed video metadata in Postgres.
    """

    messages: List[BaseMessage] = field(default_factory=list)
    videos: Dict[str, VideoMetadata] = field(default_factory=dict)


class MemoryStore:
    """
    Simple process-memory store.

    Good for demo.
    Not enough for multi-instance production.
    """

    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}

    def get_or_create(self, session_id: str) -> SessionState:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState()

        return self._sessions[session_id]

    def save_video(self, session_id: str, video: VideoMetadata) -> None:
        state = self.get_or_create(session_id)
        state.videos[video.video_id] = video

    def get_videos(self, session_id: str) -> Dict[str, VideoMetadata]:
        return self.get_or_create(session_id).videos

    def get_messages(self, session_id: str) -> List[BaseMessage]:
        return self.get_or_create(session_id).messages

    def append_message(self, session_id: str, message: BaseMessage) -> None:
        self.get_or_create(session_id).messages.append(message)


memory_store = MemoryStore()