/**
 * Video slots are fixed because the product compares exactly two inputs.
 */
export type VideoId = "A" | "B";

/**
 * Frontend representation of normalized backend video metadata.
 */
export type VideoMetadata = {
  video_id: VideoId;
  source_url: string;
  platform_id?: string | null;

  title?: string | null;
  creator?: string | null;
  creator_id?: string | null;
  follower_count?: number | null;

  views?: number | null;
  likes?: number | null;
  comments?: number | null;

  engagement_rate?: number | null;

  hashtags: string[];
  upload_date?: string | null;
  duration_seconds?: number | null;

  raw?: Record<string, unknown>;
};

/**
 * Request payload accepted by the analysis endpoint.
 */
export type AnalyzeVideosRequest = {
  video_a_url: string;
  video_b_url: string;
  session_id?: string | null;
};

/**
 * Final analysis result emitted by the backend after ingestion completes.
 */
export type AnalyzeVideosResponse = {
  session_id: string;
  videos: VideoMetadata[];
  chunks_indexed: number;
};

/**
 * Event union for the analysis SSE endpoint.
 */
export type AnalyzeStreamEvent =
  | {
    event: "progress";
    data: {
      message: string;
    };
  }
  | {
    event: "result";
    data: AnalyzeVideosResponse;
  }
  | {
    event: "error";
    data: {
      message: string;
      video_id?: VideoId;
      url?: string;
      reason?: string;
    };
  }
  | {
    event: "done";
    data: {
      message: string;
    };
  };

/**
 * Retrieved transcript source shown below assistant answers.
 */
export type SourceChunk = {
  video_id: VideoId;
  chunk_id: string;
  title?: string | null;
  creator?: string | null;
  source_url?: string | null;
  preview: string;
};

/**
 * Role of a chat message.
 */
export type ChatRole = "user" | "assistant" | "system";

/**
 * Message shape used by the local chat transcript.
 */
export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  sources?: SourceChunk[];
};

/**
 * Event union for the streaming chat endpoint.
 */
export type StreamEvent =
  | {
    event: "token";
    data: {
      text: string;
    };
  }
  | {
    event: "sources";
    data: {
      sources: SourceChunk[];
    };
  }
  | {
    event: "error";
    data: {
      message: string;
    };
  }
  | {
    event: "done";
    data: {
      message: string;
    };
  };
