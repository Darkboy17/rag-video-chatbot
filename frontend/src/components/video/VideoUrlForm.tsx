"use client";

import { type SubmitEvent, useState } from "react";
import { LinkIcon, Loader2, Play } from "lucide-react";

import { useHasHydrated } from "@/hooks/useHasHydrated";
import { VideoUrlInput } from "./VideoUrlInput";

type VideoUrlFormProps = {
  isAnalyzing: boolean;
  elapsedSeconds: number;
  onAnalyze: (videoAUrl: string, videoBUrl: string) => Promise<void>;
};

/**
 * Collects the two source URLs and starts the ingestion pipeline.
 */
export function VideoUrlForm({
  isAnalyzing,
  elapsedSeconds,
  onAnalyze,
}: VideoUrlFormProps) {

  // Collect the two source URLs.
  const [videoAUrl, setVideoAUrl] = useState("");
  const [videoBUrl, setVideoBUrl] = useState("");

  // Prevent hydration mismatch between client and server.
  const hasMounted = useHasHydrated();

  // Disable the analyze button when the video URLs are missing.
  const hasBothVideoUrls = Boolean(videoAUrl.trim() && videoBUrl.trim());

  // Disable the analyze button when the video URLs are missing.
  const isAnalyzeDisabled = hasMounted && (isAnalyzing || !hasBothVideoUrls);

  // Disable the analyze button when the video is being analyzed.
  const analyzeButtonClass = [
    "inline-flex h-9 shrink-0 items-center justify-center rounded-lg px-3 text-xs font-semibold text-white transition",
    isAnalyzing
      ? "min-w-[6.75rem] cursor-progress bg-slate-950"
      : "min-w-9 bg-slate-950 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50 sm:min-w-[6.25rem]",
  ].join(" ");

  // Display the elapsed time when the video is not being analyzed.
  const timingText = isAnalyzing
    ? `${elapsedSeconds.toFixed(1)} s elapsed`
    : elapsedSeconds > 0
      ? `Took ${elapsedSeconds.toFixed(1)} s`
      : null;

  /**
   * Start the video analysis when the form is submitted.
   * 
   * @param event - The form submit event.
   * @returns Promise<void>
   */
  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();

    // Trim at submit time so users can paste URLs with accidental whitespace.
    if (!videoAUrl.trim() || !videoBUrl.trim()) {
      return;
    }

    await onAnalyze(videoAUrl.trim(), videoBUrl.trim());
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
    >
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-cyan-50 text-cyan-700">
            <LinkIcon size={17} />
          </div>
          <div className="min-w-0">
            <h2 className="truncate text-sm font-semibold text-slate-950">
              Video inputs
            </h2>
            <p className="text-xs text-slate-500">Two source URLs</p>
          </div>
        </div>

        <div className="flex shrink-0 flex-col items-end gap-1">
          <button
            type="submit"
            disabled={isAnalyzeDisabled}
            className={analyzeButtonClass}
            aria-label={
              isAnalyzing
                ? `Analyzing videos, ${elapsedSeconds.toFixed(1)} seconds elapsed`
                : "Analyze videos"
            }
            title={isAnalyzing ? "Analyzing" : "Analyze"}
          >
            {isAnalyzing ? (
              <span className="flex items-center gap-2">
                <Loader2 className="animate-spin" size={15} />
                <span className="hidden sm:inline">Analyzing</span>
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Play size={15} />
                <span className="hidden sm:inline">Analyze</span>
              </span>
            )}
          </button>

          {timingText ? (
            <p
              aria-live="polite"
              className="min-h-4 text-right text-[11px] italic leading-none text-slate-600"
            >
              {timingText}
            </p>
          ) : null}
        </div>
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <VideoUrlInput
          label="Video A"
          value={videoAUrl}
          onChange={setVideoAUrl}
        />

        <VideoUrlInput
          label="Video B"
          value={videoBUrl}
          onChange={setVideoBUrl}
        />
      </div>
    </form>
  );
}
