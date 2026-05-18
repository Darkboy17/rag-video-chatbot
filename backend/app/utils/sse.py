import json
from typing import Any


def sse_event(event: str, data: Any) -> str:
    """
    Formats data as a Server-Sent Event.

    Frontend can listen to:
    - token
    - sources
    - error
    - done
    """

    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"
