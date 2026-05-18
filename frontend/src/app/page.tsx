"use client";

import { ChatPanel } from "@/components/chat/ChatPanel";
import { AppShell } from "@/components/layout/AppShell";
import { VideoComparisonPanel } from "@/components/video/VideoComparisonPanel";
import { VideoUrlForm } from "@/components/video/VideoUrlForm";
import { useStreamingChat } from "@/hooks/useStreamingChat";
import { useVideoAnalysis } from "@/hooks/useVideoAnalysis";

/**
 * Main workspace route that coordinates video analysis and chat state.
 */
export default function HomePage() {
  const {
    sessionId,
    videos,
    chunksIndexed,
    isAnalyzing,
    elapsedSeconds,
    error: analysisError,
    progressMessages,
    analyze,
  } = useVideoAnalysis();

  const {
    messages,
    isStreaming,
    error: chatError,
    sendMessage,
    stopStreaming,
    clearMessages,
  } = useStreamingChat(sessionId);

  async function handleAnalyze(videoAUrl: string, videoBUrl: string) {
    // A new analysis session invalidates the old chat transcript and sources.
    clearMessages();
    await analyze(videoAUrl, videoBUrl);
  }

  return (
    <AppShell>
      <div className="grid h-full min-h-0 grid-rows-[minmax(240px,0.48fr)_minmax(280px,0.52fr)] gap-4 xl:grid-cols-[minmax(360px,0.9fr)_minmax(520px,1.1fr)] xl:grid-rows-none">
        <div className="min-h-0 space-y-4 overflow-y-auto pr-1">
          <VideoUrlForm
            isAnalyzing={isAnalyzing}
            elapsedSeconds={elapsedSeconds}
            onAnalyze={handleAnalyze}
          />

          {analysisError ? (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700">
              {analysisError}
            </div>
          ) : null}

          <VideoComparisonPanel
            videos={videos}
            chunksIndexed={chunksIndexed}
            sessionId={sessionId}
            isAnalyzing={isAnalyzing}
            progressMessages={progressMessages}
          />
        </div>

        <div className="min-h-0">
          <ChatPanel
            sessionId={sessionId}
            messages={messages}
            isStreaming={isStreaming}
            error={chatError}
            onSendMessage={sendMessage}
            onStopStreaming={stopStreaming}
          />
        </div>
      </div>
    </AppShell>
  );
}
