import { CalendarDays, MessageCircle, ThumbsUp } from "lucide-react";
import { formatNumber, formatUploadDate } from "@/lib/formatters";
import type { VideoMetadata } from "@/types/api";

/**
 * Props for the {@link VideoMetaDetails} component.
 * video: The video metadata to display.
 */
type VideoMetaDetailsProps = {
  video: VideoMetadata;
};

/**
 * Secondary metrics that complement the top four stat cards.
 */
export function VideoMetaDetails({ video }: VideoMetaDetailsProps) {
  return (
    <div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-2">
      <div className="flex items-center gap-2">
        <ThumbsUp size={14} />
        <span>{formatNumber(video.likes)} likes</span>
      </div>
      <div className="flex items-center gap-2">
        <MessageCircle size={14} />
        <span>{formatNumber(video.comments)} comments</span>
      </div>
      <div className="flex items-center gap-2">
        <CalendarDays size={14} />
        <span>{formatUploadDate(video.upload_date)}</span>
      </div>
    </div>
  );
}
