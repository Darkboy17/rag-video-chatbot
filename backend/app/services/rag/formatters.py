from typing import Any, Dict, List


def build_system_prompt(video_stats: str, context: str) -> str:
    """
    Build the system prompt used for every RAG chat turn.
    """

    return f"""
You are a senior creator-strategy analyst inside a RAG chatbot.

Your job:
- Compare two social videos: Video A and Video B.
- Use transcript chunks and metadata only.
- Never invent missing stats.
- If follower count, likes, comments, or views are missing,
  say they were unavailable from extraction.
- Always cite transcript evidence using this format: [Video A: A-1] or [Video B: B-2].
- For hook/opening/first-5-seconds questions, prioritize chunks labeled
  "Opening hook (0-5 seconds)" when they are present.
- If only one video has timestamped opening-hook evidence, compare that
  available hook and state that the other video's first 5 seconds were not
  available from timestamped transcript data.
- Use metadata for engagement rate, creator, views, likes, comments,
  upload date, duration, and hashtags.
- For direct metadata questions, treat the VIDEO METADATA section as the source
  of truth. If a field has a concrete value there, never call it unavailable.
- Before answering any question about which video performed better, compare
  the metadata numbers yourself. If the user's premise is wrong, correct it
  clearly before explaining possible reasons.
- Be practical and specific.
- When asked for improvements, recommend what the lower-performing video
  should copy/adapt from the stronger video. Do not assume B underperformed.

VIDEO METADATA:
{video_stats}

RETRIEVED TRANSCRIPT CONTEXT:
{context}
""".strip()


def format_video_stats(videos: Dict[str, Any]) -> str:
    lines: List[str] = []

    for video_id, video in videos.items():
        hashtags = ", ".join(video.hashtags) if video.hashtags else "Unavailable"

        lines.append(
            f"""
Video {video_id}
Title: {_format_optional(video.title)}
Creator: {_format_optional(video.creator)}
Creator ID: {_format_optional(video.creator_id)}
Follower Count: {_format_number(video.follower_count)}
Views: {_format_number(video.views)}
Likes: {_format_number(video.likes)}
Comments: {_format_number(video.comments)}
Engagement Rate: {_format_optional(video.engagement_rate)}
Hashtags: {hashtags}
Upload Date: {_format_optional(video.upload_date)}
Duration Seconds: {_format_number(video.duration_seconds)}
Source URL: {video.source_url}
""".strip()
        )

    comparison = _format_engagement_comparison(videos)
    if comparison:
        lines.append(comparison)

    return "\n\n".join(lines)


def _format_engagement_comparison(videos: Dict[str, Any]) -> str | None:
    video_a = videos.get("A")
    video_b = videos.get("B")

    if not video_a or not video_b:
        return None

    engagement_a = video_a.engagement_rate
    engagement_b = video_b.engagement_rate

    if engagement_a is None or engagement_b is None:
        return (
            "Engagement Comparison: unavailable because at least one "
            "engagement rate could not be extracted."
        )

    if engagement_a == engagement_b:
        return (
            "Engagement Comparison: Video A and Video B have the same "
            f"engagement rate ({engagement_a})."
        )

    winner = "A" if engagement_a > engagement_b else "B"
    loser = "B" if winner == "A" else "A"
    winner_rate = engagement_a if winner == "A" else engagement_b
    loser_rate = engagement_b if winner == "A" else engagement_a

    return (
        "Engagement Comparison: Video "
        f"{winner} has higher engagement than Video {loser} "
        f"({winner_rate} vs {loser_rate})."
    )


def format_context(docs) -> str:
    if not docs:
        return "No relevant transcript chunks found."

    blocks = []

    for doc in docs:
        video_id = doc.metadata.get("video_id")
        chunk_id = doc.metadata.get("chunk_id")

        blocks.append(
            f"""
[Video {video_id}: {chunk_id}]
{doc.page_content}
""".strip()
        )

    return "\n\n".join(blocks)


def format_sources(docs) -> List[dict]:
    return [
        {
            "video_id": doc.metadata.get("video_id"),
            "chunk_id": doc.metadata.get("chunk_id"),
            "title": doc.metadata.get("title"),
            "creator": doc.metadata.get("creator"),
            "source_url": doc.metadata.get("source_url"),
            "preview": doc.page_content[:240],
        }
        for doc in docs
    ]


def _format_optional(value) -> str:
    if value is None or value == "":
        return "Unavailable from extraction"

    return str(value)


def _format_number(value) -> str:
    if value is None:
        return "Unavailable from extraction"

    return f"{value:,}"
