/**
 * Props for the {@link HashtagList} component.
 * hashtags: An array of extracted hashtags.
 */
type HashtagListProps = {
  hashtags: string[];
};

/**
 * Displays a bounded list of extracted hashtags without letting long tag lists
 * stretch the video card.
 */
export function HashtagList({ hashtags }: HashtagListProps) {
  return (
    <div className="mt-3 max-h-16 overflow-y-auto">
      {hashtags.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {hashtags.slice(0, 10).map((tag) => (
            <span
              key={tag}
              className="rounded-md bg-slate-100 px-2 py-1 text-[11px] font-medium text-slate-600"
            >
              {tag}
            </span>
          ))}
        </div>
      ) : (
        <p className="text-xs text-slate-400">No hashtags</p>
      )}
    </div>
  );
}
