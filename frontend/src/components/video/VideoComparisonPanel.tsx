"use client";



import { AnalysisProgressLog } from "./AnalysisProgressLog";
import { ComparisonSummary } from "./ComparisonSummary";
import type { VideoMetadata } from "@/types/api";
import { useEffect, useRef } from "react";
import { VideoCard } from "./VideoCard";


/**
 * Props for the {@link VideoComparisonPanel} component.
 * videos: An array of video metadata.
 * chunksIndexed: The number of video chunks indexed.
 * sessionId: The current analysis session ID.
 * isAnalyzing: A boolean indicating whether the analysis is in progress.
 * progressMessages: An array of strings representing the analysis progress messages.
 */
type VideoComparisonPanelProps = {
  videos: VideoMetadata[];
  chunksIndexed: number;
  sessionId: string | null;
  isAnalyzing: boolean;
  progressMessages: string[];
};

/**
 * Switches between pre-result analysis progress and post-result video cards.
 */
export function VideoComparisonPanel({
  videos,
  chunksIndexed,
  sessionId,
  isAnalyzing,
  progressMessages,
}: VideoComparisonPanelProps) {

  // Ref to the progress log's HTML list element
  const progressListRef = useRef<HTMLOListElement | null>(null);

  // Scroll the progress log to the bottom when new messages are added
  useEffect(() => {
    const progressList = progressListRef.current;

    if (!progressList || progressMessages.length === 0) {
      return;
    }

    // Keep the progress log pinned to the newest backend SSE event while the
    // user waits for analysis to finish.
    progressList.scrollTo({
      top: progressList.scrollHeight,
      behavior: "smooth",
    });
  }, [progressMessages.length]);

  // Render the analysis progress log if there are no videos
  if (videos.length === 0) {
    return (
      <AnalysisProgressLog
        isAnalyzing={isAnalyzing}
        progressMessages={progressMessages}
        progressListRef={progressListRef}
      />
    );
  }

  return (
    <section className="space-y-4">
      <ComparisonSummary
        videos={videos}
        chunksIndexed={chunksIndexed}
        sessionId={sessionId}
      />

      <div className="grid gap-4 2xl:grid-cols-2">
        {videos.map((video) => (
          <VideoCard key={video.video_id} video={video} />
        ))}
      </div>
    </section>
  );
}