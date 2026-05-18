import type { SourceChunk } from "@/types/api";
import { ExternalLink } from "lucide-react";

/**
 * Props for the {@link SourceList} component.
 * sources: An array of source chunks.
 */
type SourceListProps = {
  sources: SourceChunk[];
};

/**
 * Collapsible evidence list attached to assistant messages.
 */
export function SourceList({ sources }: SourceListProps) {

  // If there are no sources, do not render.
  if (!sources.length) {
    return null;
  }

  return (
    <details className="mt-3 rounded-lg border border-slate-200 bg-white">
      <summary className="cursor-pointer px-3 py-2 text-xs font-semibold text-slate-600">
        Sources ({sources.length})
      </summary>

      <div className="max-h-48 space-y-2 overflow-y-auto border-t border-slate-200 p-2">
        {sources.map((source) => (
          <div
            key={`${source.video_id}-${source.chunk_id}`}
            className="rounded-lg bg-slate-50 p-2.5 text-sm"
          >
            <div className="mb-1 flex items-center justify-between gap-3">
              <p className="text-xs font-semibold text-slate-900">
                Video {source.video_id}: {source.chunk_id}
              </p>

              {source.source_url ? (
                <a
                  href={source.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-slate-400 transition hover:text-slate-950"
                  aria-label="Open source video"
                >
                  <ExternalLink size={14} />
                </a>
              ) : null}
            </div>

            <p className="line-clamp-2 text-xs leading-5 text-slate-500">
              {source.preview}
            </p>
          </div>
        ))}
      </div>
    </details>
  );
}
