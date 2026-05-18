import asyncio
from typing import Any, Callable

from app.utils.sse import sse_event

SseProducer = Callable[
    [asyncio.AbstractEventLoop, asyncio.Queue[tuple[str, Any]]],
    None,
]


async def stream_threaded_sse(producer: SseProducer):
    """
    Bridge blocking work into an async SSE generator.

    The producer runs in a worker thread and pushes `(event, data)` tuples into
    the async queue through `loop.call_soon_threadsafe`.
    """

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[tuple[str, Any]] = asyncio.Queue()
    task = asyncio.create_task(asyncio.to_thread(producer, loop, queue))

    try:
        while True:
            event, data = await queue.get()
            yield sse_event(event, data)

            if event == "done":
                break
    finally:
        await task


def queue_event(
    loop: asyncio.AbstractEventLoop,
    queue: asyncio.Queue[tuple[str, Any]],
    event: str,
    data: Any,
) -> None:
    loop.call_soon_threadsafe(queue.put_nowait, (event, data))
