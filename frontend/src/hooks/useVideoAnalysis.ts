"use client";


import type { AnalyzeVideosResponse, VideoMetadata } from "@/types/api";
import { getAnalyzeStreamResponse } from "@/lib/api";
import { useEffect, useRef, useState } from "react";
import { readAnalyzeSseStream } from "@/lib/sse";


/**
 * Props for the {@link useVideoAnalysis} hook.
 * sessiionId: A string representing the current analysis session ID.
 * videos: An array of video metadata.
 * chunksIndexed: The number of video chunks indexed.
 * isAnalyzing: A boolean indicating whether the analysis is in progress.
 * elapsedSeconds: The number of seconds elapsed since the analysis started.
 * error: A string representing the analysis error, if any.
 * progressMessages: An array of strings representing the analysis progress messages.
 */
type VideoAnalysisState = {
    sessionId: string | null;
    videos: VideoMetadata[];
    chunksIndexed: number;
    isAnalyzing: boolean;
    elapsedSeconds: number;
    error: string | null;
    progressMessages: string[];
};


/**
 * Props for the {@link useVideoAnalysis} hook.
 * followerCount: An optional number representing the follower count of the video.
 */
type RawVideoMetadata = VideoMetadata & {
    followerCount?: unknown;
};

/**
 * Coerce a value into a number, or null if the value is not a number.
 * @returns A number or null.
 */
function coerceOptionalNumber(value: unknown): number | null | undefined {
    // Be defensive about older/camelCase API fields and stringified numbers.
    if (value === null || value === undefined) {
        return value;
    }

    if (typeof value === "number") {
        return Number.isFinite(value) ? value : null;
    }

    if (typeof value === "string") {
        const numericValue = Number(value.replace(/,/g, ""));
        return Number.isFinite(numericValue) ? numericValue : null;
    }

    return null;
}

/**
 * Normalizes a video metadata object.
 * @returns A normalized video metadata object.
 */
function normalizeVideoMetadata(video: VideoMetadata): VideoMetadata {
    // Keep the frontend tolerant of API payloads produced before the snake_case
    // contract was fully settled.
    const rawVideo = video as RawVideoMetadata;
    const followerCount = coerceOptionalNumber(
        video.follower_count ?? rawVideo.followerCount
    );

    return {
        ...video,
        follower_count: followerCount ?? null,
    };
}

/**
 * Normalizes a video analysis response.
 * @returns A normalized video analysis response.
 */
function normalizeAnalyzeResponse(
    response: AnalyzeVideosResponse
): AnalyzeVideosResponse {
    return {
        ...response,
        videos: response.videos.map(normalizeVideoMetadata),
    };
}

/**
 * Runs video analysis, tracks SSE progress, and exposes normalized results.
 */
export function useVideoAnalysis() {
    // Ref to the current analysis start time
    const analysisStartedAtRef = useRef<number | null>(null);

    // Get the number of seconds elapsed since the analysis started
    function getElapsedSeconds() {
        if (!analysisStartedAtRef.current) {
            return 0;
        }

        return (performance.now() - analysisStartedAtRef.current) / 1000;
    }

    // State for the current analysis
    const [state, setState] = useState<VideoAnalysisState>({
        sessionId: null,
        videos: [],
        chunksIndexed: 0,
        isAnalyzing: false,
        elapsedSeconds: 0,
        error: null,
        progressMessages: [],
    });

    // Update elapsed time while the stream is active
    useEffect(() => {
        if (!state.isAnalyzing) {
            return;
        }

        // Update visible elapsed time while the stream is active without tying
        // timing state to individual backend progress events.
        const intervalId = window.setInterval(() => {
            setState((current) => ({
                ...current,
                elapsedSeconds: getElapsedSeconds(),
            }));
        }, 100);

        return () => window.clearInterval(intervalId);
    }, [state.isAnalyzing]);

    // Function to start video analysis
    async function analyze(videoAUrl: string, videoBUrl: string) {

        // Ref to the current analysis start time
        analysisStartedAtRef.current = performance.now();

        setState((current) => ({
            ...current,
            videos: [],
            chunksIndexed: 0,
            isAnalyzing: true,
            elapsedSeconds: 0,
            error: null,
            progressMessages: ["Starting analysis."],
        }));

        try {
            const response = await getAnalyzeStreamResponse({
                video_a_url: videoAUrl,
                video_b_url: videoBUrl,
            });

            // Local state for the current analysis
            let analysisResult: AnalyzeVideosResponse | null = null;
            let streamError: Error | null = null;

            // The backend streams progress first, then emits one final result
            // payload. We keep both locals so completion can be validated after
            // the stream closes.
            await readAnalyzeSseStream(response, {
                onProgress(message) {
                    setState((current) => ({
                        ...current,
                        progressMessages: [...current.progressMessages, message],
                    }));
                },
                onResult(event) {
                    const normalizedResult = normalizeAnalyzeResponse(event.data);
                    analysisResult = normalizedResult;

                    setState((current) => ({
                        ...current,
                        sessionId: normalizedResult.session_id,
                        videos: normalizedResult.videos,
                        chunksIndexed: normalizedResult.chunks_indexed,
                        error: null,
                    }));
                },
                onError(event) {
                    const message =
                        event.data.reason ??
                        event.data.message ??
                        "Something went wrong while analyzing videos.";

                    streamError = new Error(message);

                    setState((current) => ({
                        ...current,
                        error: message,
                        progressMessages: [...current.progressMessages, `Failed: ${message}`],
                    }));
                },
            });

            // If the stream closed with an error, throw it.
            if (streamError) {
                throw streamError;
            }

            // If the stream closed without returning a result, throw an error.
            if (!analysisResult) {
                throw new Error("Analysis finished without returning a result.");
            }

            // Get the final elapsed time
            const finalElapsedSeconds = getElapsedSeconds();

            setState((current) => ({
                ...current,
                isAnalyzing: false,
                elapsedSeconds: finalElapsedSeconds,
                error: null,
            }));

            return analysisResult;
        } catch (error) {
            const message =
                error instanceof Error
                    ? error.message
                    : "Something went wrong while analyzing videos.";

            const finalElapsedSeconds = getElapsedSeconds();

            setState((current) => ({
                ...current,
                isAnalyzing: false,
                elapsedSeconds: finalElapsedSeconds,
                error: message,
                progressMessages:
                    current.progressMessages.length > 0
                        ? current.progressMessages
                        : [`Failed: ${message}`],
            }));

            throw error;
        } finally {
            analysisStartedAtRef.current = null;
        }
    }

    /**
     * Resets the analysis state.
     * @returns A function to reset the analysis state.
     */
    function resetAnalysis() {
        setState({
            sessionId: null,
            videos: [],
            chunksIndexed: 0,
            isAnalyzing: false,
            elapsedSeconds: 0,
            error: null,
            progressMessages: [],
        });
    }

    return {
        ...state,
        analyze,
        resetAnalysis,
    };
}