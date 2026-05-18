import type {
  AnalyzeVideosRequest,
  AnalyzeVideosResponse,
} from "@/types/api";

// Base URL for API requests.
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/**
 * Error type that preserves the HTTP status for UI or debugging decisions.
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Generic API request with JSON serialization.
 * @returns The parsed JSON response.
 */
async function requestJson<TResponse>(
  path: string,
  options: RequestInit
): Promise<TResponse> {

  // Plain JSON requests share error parsing; streaming endpoints stay separate
  // because callers need direct access to the Response body.
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const errorBody = await response.json();
      message = errorBody.detail ?? errorBody.message ?? message;
    } catch {
      // Keep default error if response is not JSON.
    }

    throw new ApiError(message, response.status);
  }

  return response.json() as Promise<TResponse>;
}

/**
 * Non-streaming analysis endpoint kept for simple JSON clients and tests.
 */
export function analyzeVideos(
  payload: AnalyzeVideosRequest
): Promise<AnalyzeVideosResponse> {
  return requestJson<AnalyzeVideosResponse>("/api/videos/analyze", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * Starts video analysis as an SSE response so progress can update live.
 */
export function getAnalyzeStreamResponse(
  payload: AnalyzeVideosRequest,
  signal?: AbortSignal
): Promise<Response> {
  return fetch(`${API_BASE_URL}/api/videos/analyze/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(payload),
    signal,
  });
}

/**
 * Starts an SSE chat turn for the current analysis session.
 */
export function getChatStreamResponse(
  sessionId: string,
  message: string,
  signal?: AbortSignal
): Promise<Response> {
  return fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({
      session_id: sessionId,
      message,
    }),
    signal,
  });
}
