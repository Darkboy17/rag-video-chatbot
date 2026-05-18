import { VideoCreatorLine } from "./VideoCreatorLine";
import { VideoMetaDetails } from "./VideoMetaDetails";
import { VideoStatsGrid } from "./VideoStatsGrid";
import type { VideoMetadata } from "@/types/api";
import { VideoPreview } from "./VideoPreview";
import { HashtagList } from "./HashtagList";

/**
 * Props for the {@link VideoCard} component.
 * video: The video metadata to display.
 */
type VideoCardProps = {
  video: VideoMetadata;
};

/**
 * Full metadata card for one analyzed video.
 */
export function VideoCard({ video }: VideoCardProps) {

  // Determine whether the video has metadata errors
  const hasMetadataError =
    typeof video.raw?.error === "string" || video.title === "Metadata unavailable";

  // Get the video thumbnail
  const thumbnail =
    typeof video.raw?.thumbnail === "string" ? video.raw.thumbnail : null;

  return (
    <article className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <VideoPreview
        sourceUrl={video.source_url}
        thumbnail={thumbnail}
        videoId={video.video_id}
      />

      <div className="p-4">
        <h3 className="line-clamp-2 text-sm font-semibold leading-5 text-slate-950">
          {video.title ?? "Untitled video"}
        </h3>

        <VideoCreatorLine
          creator={video.creator}
          creatorId={video.creator_id}
        />

        {hasMetadataError ? (
          <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
            Metadata partially unavailable.
          </div>
        ) : null}

        <VideoStatsGrid video={video} />
        <VideoMetaDetails video={video} />
        <HashtagList hashtags={video.hashtags} />
      </div>
    </article>
  );
}
