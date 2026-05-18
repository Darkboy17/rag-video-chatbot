import type { AnalyzeStreamEvent, StreamEvent } from "@/types/api";

/**
 * Parsed SSE frame with an event name and JSON payload.
 * event: string
 * data: unknown
 */
type ParsedSseMessage = {
    event: string;
    data: unknown;
};

/**
 * Parse a SSE block into an event name and JSON payload.
 * 
 * @param block Raw SSE block.
 * @returns Parsed SSE frame with an event name and JSON payload, or null.
 */
function parseSseBlock(block: string): ParsedSseMessage | null {
    // SSE events are delivered as text frames separated by blank lines. The
    // backend emits one event name plus JSON data for each frame.
    const lines = block.split("\n");

    let eventName = "";
    const dataLines: string[] = [];

    for (const line of lines) {
        if (line.startsWith("event:")) {
            eventName = line.replace("event:", "").trim();
        }

        if (line.startsWith("data:")) {
            dataLines.push(line.replace("data:", "").trim());
        }
    }

    if (!eventName || dataLines.length === 0) {
        return null;
    }

    try {
        return {
            event: eventName,
            data: JSON.parse(dataLines.join("\n")),
        };
    } catch {
        return null;
    }
}

/**
 * Checks whether a parsed SSE frame belongs to the chat stream event set.
 *
 * @param message Parsed SSE frame with an event name and JSON payload.
 * @returns True when the frame can be handled as a chat stream event.
 */
function isStreamEvent(message: ParsedSseMessage): message is StreamEvent {
    // Narrow unknown SSE frames before reading typed payload fields.
    return ["token", "sources", "error", "done"].includes(message.event);
}

/**
 * Checks whether a parsed SSE frame belongs to the analyze stream event set.
 *
 * @param message Parsed SSE frame with an event name and JSON payload.
 * @returns True when the frame can be handled as an analyze stream event.
 */
function isAnalyzeStreamEvent(
    message: ParsedSseMessage
): message is AnalyzeStreamEvent {
    // Analyze streams use a different event vocabulary from chat streams.
    return ["progress", "result", "error", "done"].includes(message.event);
}

/**
 * Read a chat SSE stream and dispatch typed events to UI handlers.
 */
export async function readSseStream(
    response: Response,
    handlers: {
        onToken?: (token: string) => void | Promise<void>;
        onSources?: (sources: StreamEvent & { event: "sources" }) => void;
        onError?: (message: string) => void;
        onDone?: () => void;
    }
): Promise<void> {
    if (!response.ok) {
        throw new Error(`Chat stream failed with status ${response.status}`);
    }

    if (!response.body) {
        throw new Error("Chat stream response has no body.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");

    let buffer = "";

    while (true) {
        const { value, done } = await reader.read();

        if (done) {
            break;
        }

        buffer += decoder.decode(value, { stream: true });

        // The last split item may be an incomplete frame, so keep it buffered
        // until the next network chunk arrives.
        const blocks = buffer.split("\n\n");

        buffer = blocks.pop() ?? "";

        for (const block of blocks) {
            const parsed = parseSseBlock(block);

            if (!parsed || !isStreamEvent(parsed)) {
                continue;
            }

            if (parsed.event === "token") {
                await handlers.onToken?.(parsed.data.text);
            }

            if (parsed.event === "sources") {
                handlers.onSources?.(parsed as StreamEvent & { event: "sources" });
            }

            if (parsed.event === "error") {
                handlers.onError?.(parsed.data.message);
            }

            if (parsed.event === "done") {
                handlers.onDone?.();
            }
        }
    }
}

/**
 * Read the analysis SSE stream and dispatch progress/result/error events.
 */
export async function readAnalyzeSseStream(
    response: Response,
    handlers: {
        onProgress?: (message: string) => void;
        onResult?: (result: AnalyzeStreamEvent & { event: "result" }) => void;
        onError?: (event: AnalyzeStreamEvent & { event: "error" }) => void;
        onDone?: () => void;
    }
): Promise<void> {
    if (!response.ok) {
        throw new Error(`Analyze stream failed with status ${response.status}`);
    }

    if (!response.body) {
        throw new Error("Analyze stream response has no body.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");

    let buffer = "";

    while (true) {
        const { value, done } = await reader.read();

        if (done) {
            break;
        }

        buffer += decoder.decode(value, { stream: true });

        // Preserve partial frames between chunks for the same reason as chat
        // streaming: network chunks do not necessarily align with SSE frames.
        const blocks = buffer.split("\n\n");

        buffer = blocks.pop() ?? "";

        for (const block of blocks) {
            const parsed = parseSseBlock(block);

            if (!parsed || !isAnalyzeStreamEvent(parsed)) {
                continue;
            }

            if (parsed.event === "progress") {
                handlers.onProgress?.(parsed.data.message);
            }

            if (parsed.event === "result") {
                handlers.onResult?.(parsed as AnalyzeStreamEvent & { event: "result" });
            }

            if (parsed.event === "error") {
                handlers.onError?.(parsed as AnalyzeStreamEvent & { event: "error" });
            }

            if (parsed.event === "done") {
                handlers.onDone?.();
            }
        }
    }
}
