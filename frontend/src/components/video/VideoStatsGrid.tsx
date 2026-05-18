import {
  formatDuration,
  formatNumber,
  formatPercent,
} from "@/lib/formatters";
import type { VideoMetadata } from "@/types/api";

/**
 * Props for the {@link VideoStatsGrid} component.
 * video: The video metadata to display.
 */
type VideoStatsGridProps = {
  video: VideoMetadata;
};

/**
 * Reusable stat tile for high-priority video metrics.
 */
function StatItem({ label, value }: { label: string; value: string; }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
      <p className="text-[11px] font-medium uppercase text-slate-400">
        {label}
      </p>
      <p className="mt-1 text-sm font-semibold text-slate-950">{value}</p>
    </div>
  );
}

/**
 * The four primary metrics shown at the top of each video card.
 */
export function VideoStatsGrid({ video }: VideoStatsGridProps) {
  return (
    <div className="mt-4 grid grid-cols-2 gap-2">
      <StatItem label="Views" value={formatNumber(video.views)} />
      <StatItem label="Engagement" value={formatPercent(video.engagement_rate)} />
      <StatItem label="Followers" value={formatNumber(video.follower_count)} />
      <StatItem label="Duration" value={formatDuration(video.duration_seconds)} />
    </div>
  );
}