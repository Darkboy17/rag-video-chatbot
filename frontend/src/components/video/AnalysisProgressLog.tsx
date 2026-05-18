import { CheckCircle2, FileText, Loader2 } from "lucide-react";
import type { RefObject } from "react";

/**
 * Props for the {@link AnalysisProgressLog} component.
 * isAnalyzing: A boolean indicating whether the video is currently being analyzed.
 * progressMessages: An array of strings representing the analysis progress messages.
 * progressListRef: A reference to the progress log's HTML list element.
 */
type AnalysisProgressLogProps = {
  isAnalyzing: boolean;
  progressMessages: string[];
  progressListRef: RefObject<HTMLOListElement | null>;
};

/**
 * Shows the analysis lifecycle before video metadata is available.
 */
export function AnalysisProgressLog({
  isAnalyzing,
  progressMessages,
  progressListRef,
}: AnalysisProgressLogProps) {

  // Render the analysis progress log only when the video is being analyzed.
  if (!isAnalyzing && progressMessages.length === 0) {
    return (
      <section className="rounded-lg border border-dashed border-slate-300 bg-white p-4 shadow-sm">
        <div className="py-2 text-center">
          <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
            <FileText size={20} />
          </div>
          <h2 className="text-sm font-semibold text-slate-950">
            No analysis yet
          </h2>
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-lg border border-dashed border-slate-300 bg-white p-4 shadow-sm">
      <div>
        <div className="mb-3 flex items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-2">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-cyan-50 text-cyan-700">
              {isAnalyzing ? (
                <Loader2 className="animate-spin" size={18} />
              ) : (
                <CheckCircle2 size={18} />
              )}
            </div>
            <div className="min-w-0">
              <h2 className="truncate text-sm font-semibold text-slate-950">
                {isAnalyzing ? "Analyzing videos" : "Analysis log"}
              </h2>
              <p className="text-xs text-slate-500">
                {progressMessages.length} step{progressMessages.length === 1 ? "" : "s"}
              </p>
            </div>
          </div>
        </div>

        <ol
          ref={progressListRef}
          className="max-h-56 space-y-2 overflow-y-auto pr-1"
        >
          {progressMessages.map((message, index) => {
            // The newest event gets a live dot while ingestion is still running;
            // older events render as completed checkpoints.
            const isLatest = index === progressMessages.length - 1;

            return (
              <li
                key={`${message}-${index}`}
                className="flex gap-2 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-left"
              >
                <span className="mt-1 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-white text-slate-400 ring-1 ring-slate-200">
                  {isLatest && isAnalyzing ? (
                    <span className="h-1.5 w-1.5 rounded-full bg-cyan-600" />
                  ) : (
                    <CheckCircle2 size={11} />
                  )}
                </span>
                <span className="text-xs leading-5 text-slate-700">
                  {message}
                </span>
              </li>
            );
          })}
        </ol>
      </div>
    </section>
  );
}
