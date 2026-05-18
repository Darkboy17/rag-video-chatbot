from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_ingestion_service
from app.schemas.video import AnalyzeVideosRequest, AnalyzeVideosResponse
from app.services.ingestion.service import VideoIngestionError
from app.utils.streaming import queue_event, stream_threaded_sse

# A router for video analysis
router = APIRouter(tags=["Video analysis"])

# The message to return when a video analysis fails
ANALYSIS_FAILURE_MESSAGE = (
    "Video analysis failed while fetching or transcribing a video."
)


@router.post("/videos/analyze", response_model=AnalyzeVideosResponse)
def analyze_videos(payload: AnalyzeVideosRequest):
    """
    Run the full ingestion pipeline and return the final result as JSON.
    """

    try:
        return get_ingestion_service().ingest_two_videos(payload)
    except VideoIngestionError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": ANALYSIS_FAILURE_MESSAGE,
                "video_id": exc.video_id,
                "url": exc.url,
                "reason": exc.reason,
            },
        ) from exc


@router.post("/videos/analyze/stream")
async def analyze_videos_stream(payload: AnalyzeVideosRequest):
    """
    Stream ingestion progress events followed by the final analysis payload.
    """

    async def event_stream():

        def producer(loop, queue) -> None:

            def progress(message: str) -> None:
                queue_event(loop, queue, "progress", {"message": message})

            try:
                result = get_ingestion_service().ingest_two_videos(
                    payload,
                    on_progress=progress,
                )
                queue_event(loop, queue, "result",
                            result.model_dump(mode="json"))
            except VideoIngestionError as exc:
                queue_event(
                    loop,
                    queue,
                    "error",
                    {
                        "message": ANALYSIS_FAILURE_MESSAGE,
                        "video_id": exc.video_id,
                        "url": exc.url,
                        "reason": exc.reason,
                    },
                )
            except Exception as exc:
                queue_event(loop, queue, "error", {"message": str(exc)})
            finally:
                queue_event(loop, queue, "done", {"message": "completed"})

        async for event in stream_threaded_sse(producer):
            yield event

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
