/* eslint-disable @next/next/no-img-element */
import { ExternalLink } from "lucide-react";

/**
 * Props for the {@link VideoPreview} component.
 * sourceUrl: The URL of the video source.
 * thumbnail: The URL of the video thumbnail.
 * videoId: The ID of the video.
 */
type VideoPreviewProps = {
  sourceUrl: string;
  thumbnail: string | null;
  videoId: string;
};

/**
 * Thumbnail/header area for a video card with direct source linking.
 */
export function VideoPreview({ sourceUrl, thumbnail, videoId }: VideoPreviewProps) {
  return (
    <div className="relative aspect-video bg-slate-100">
      {thumbnail ? (
        <img
          src={thumbnail}
          alt=""
          className="h-full w-full object-cover"
          loading="lazy"
          referrerPolicy="no-referrer"
        />
      ) : (
        <div className="flex h-full items-center justify-center text-sm font-medium text-slate-400">
          Video {videoId}
        </div>
      )}

      <div className="absolute left-3 top-3 rounded-lg bg-slate-950 px-2 py-1 text-xs font-semibold text-white shadow-sm">
        Video {videoId}
      </div>

      <a
        href={sourceUrl}
        target="_blank"
        rel="noreferrer"
        className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-lg bg-white/95 text-slate-600 shadow-sm transition hover:text-slate-950"
        aria-label={`Open Video ${videoId}`}
        title={`Open Video ${videoId}`}
      >
        <ExternalLink size={16} />
      </a>
    </div>
  );
}
