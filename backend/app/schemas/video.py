from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class AnalyzeVideosRequest(BaseModel):
    """
    Request body for comparing two social videos in a single analysis session.
    """

    video_a_url: str = Field(..., description="URL for Video A")
    video_b_url: str = Field(..., description="URL for Video B")
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID. If missing, backend creates one.",
    )

    @field_validator("session_id", mode="before")
    @classmethod
    def normalize_session_id(cls, value):
        # Treat blank Swagger placeholders as "no session" so the backend can
        # create a fresh session ID instead of storing data under a fake value.
        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()

            if not value or value.lower() == "string":
                return None

        return value

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "video_a_url": "https://www.youtube.com/shorts/0hX1srSF9Ss",
                    "video_b_url": "https://www.youtube.com/shorts/YI63gPfjDIg",
                }
            ]
        }
    }


class VideoMetadata(BaseModel):
    """
    Normalized metadata returned by platform-specific video extractors.
    """

    # Stable IDs and source references used by transcript chunks and memory.
    video_id: str
    source_url: str
    platform_id: Optional[str] = None

    # Creator/profile details.
    title: Optional[str] = None
    creator: Optional[str] = None
    creator_id: Optional[str] = None
    follower_count: Optional[int] = None

    # Engagement metrics used by the comparison formatter.
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None

    engagement_rate: Optional[float] = None

    # Content descriptors and original extractor payload.
    hashtags: List[str] = []
    upload_date: Optional[str] = None
    duration_seconds: Optional[int] = None

    raw: Dict[str, Any] = {}


class AnalyzeVideosResponse(BaseModel):
    """
    Final ingestion response returned after metadata and transcript chunks are saved.
    """

    session_id: str
    videos: List[VideoMetadata]
    chunks_indexed: int
