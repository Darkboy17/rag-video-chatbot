import { formatNumber, formatPercent } from "@/lib/formatters";
import { BarChart3, Database, Hash } from "lucide-react";
import type { VideoMetadata } from "@/types/api";

/**
 * Props for the {@link ComparisonSummary} component.
 * videos: An array of video metadata.
 * chunksIndexed: The number of video chunks indexed.
 * sessionId: The current analysis session ID.
 */
type ComparisonSummaryProps = {
  videos: VideoMetadata[];
  chunksIndexed: number;
  sessionId: string | null;
};

/**
 * Compact rollup of the current analysis session and headline winners.
 */
export function ComparisonSummary({
  videos,
  chunksIndexed,
  sessionId,
}: ComparisonSummaryProps) {

  // Sort videos by views and engagement rate
  const topByViews = [...videos].sort((a, b) => (b.views ?? 0) - (a.views ?? 0))[0];
  const topByEngagement = [...videos].sort(
    (a, b) => (b.engagement_rate ?? 0) - (a.engagement_rate ?? 0)
  )[0];

  // Shorten session ID
  const shortSessionId = sessionId
    ? `${sessionId.slice(0, 8)}${sessionId.length > 8 ? "..." : ""}`
    : "Pending";

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="min-w-0">
          <h2 className="truncate text-sm font-semibold text-slate-950">
            Video comparison
          </h2>
          <p className="text-xs text-slate-500">Session {shortSessionId}</p>
        </div>

        <div className="flex items-center gap-2 rounded-lg bg-slate-100 px-2.5 py-1.5 text-xs font-medium text-slate-700">
          <Database size={14} />
          {chunksIndexed} chunks
        </div>
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        <div className="rounded-lg border border-cyan-100 bg-cyan-50 px-3 py-2">
          <div className="flex items-center gap-2 text-xs font-medium text-cyan-800">
            <BarChart3 size={14} />
            Views leader
          </div>
          <p className="mt-1 text-sm font-semibold text-slate-950">
            Video {topByViews?.video_id} - {formatNumber(topByViews?.views)}
          </p>
        </div>

        <div className="rounded-lg border border-emerald-100 bg-emerald-50 px-3 py-2">
          <div className="flex items-center gap-2 text-xs font-medium text-emerald-800">
            <Hash size={14} />
            Engagement leader
          </div>
          <p className="mt-1 text-sm font-semibold text-slate-950">
            Video {topByEngagement?.video_id} -{" "}
            {formatPercent(topByEngagement?.engagement_rate)}
          </p>
        </div>
      </div>
    </div>
  );
}
