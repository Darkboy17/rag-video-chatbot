/**
 * @fileoverview Labeled URL input used for both comparison targets.
 * label: The label to display above the input.
 * value: The current value of the input.
 * onChange: A function to call when the value changes.
 */
type VideoUrlInputProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
};

/**
 * Labeled URL input used for both comparison targets.
 */
export function VideoUrlInput({ label, value, onChange }: VideoUrlInputProps) {
  return (
    <label className="block">
      <span className="text-xs font-medium text-slate-600">
        {label}
      </span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="https://www.youtube.com/shorts/..."
        className="mt-1.5 h-10 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm outline-none transition focus:border-cyan-500 focus:bg-white focus:ring-2 focus:ring-cyan-500/10"
      />
    </label>
  );
}
