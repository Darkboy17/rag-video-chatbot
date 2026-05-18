import { User } from "lucide-react";

/**
 * Props for the {@link VideoCreatorLine} component.
 * creator: The name of the video creator.
 * creatorId: The ID of the video creator.
 */
type VideoCreatorLineProps = {
  creator?: string | null;
  creatorId?: string | null;
};

/**
 * Creator identity row for a video card.
 */
export function VideoCreatorLine({
  creator,
  creatorId,
}: VideoCreatorLineProps) {
  return (
    <div className="mt-2 flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
      <span className="inline-flex min-w-0 items-center gap-1.5">
        <User size={13} />
        <span className="truncate">
          {creator ?? "Creator unavailable"}
        </span>
      </span>
      {creatorId ? <span>{creatorId}</span> : null}
    </div>
  );
}
