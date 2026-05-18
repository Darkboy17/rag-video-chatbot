/**
 * Lightweight animated placeholder shown before the first assistant token.
 */
export function TypingIndicator() {
  return (
    <div
      className="flex h-6 items-center gap-1"
      aria-label="Assistant is typing"
      role="status"
    >
      <span className="h-1.5 w-1.5 animate-[typing-bounce_920ms_cubic-bezier(0.45,0,0.25,1)_infinite] rounded-full bg-slate-500 [animation-delay:-0.42s] motion-reduce:animate-none" />
      <span className="h-1.5 w-1.5 animate-[typing-bounce_920ms_cubic-bezier(0.45,0,0.25,1)_infinite] rounded-full bg-slate-500 [animation-delay:-0.21s] motion-reduce:animate-none" />
      <span className="h-1.5 w-1.5 animate-[typing-bounce_920ms_cubic-bezier(0.45,0,0.25,1)_infinite] rounded-full bg-slate-500 motion-reduce:animate-none" />
    </div>
  );
}
