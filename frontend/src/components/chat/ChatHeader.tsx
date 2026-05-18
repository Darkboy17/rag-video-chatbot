import { Bot } from "lucide-react";

/**
 * Props for the {@link ChatHeader} component.
 * sessionId: A string representing the current chat session ID.
 * isStreaming: A boolean indicating whether the chat is currently streaming.
 */
type ChatHeaderProps = {
  sessionId: string | null;
  isStreaming: boolean;
};

/**
 * Compact chat status header with a shortened session identifier.
 */
export function ChatHeader({ sessionId, isStreaming }: ChatHeaderProps) {
  const shortSessionId = sessionId
    ? `${sessionId.slice(0, 8)}${sessionId.length > 8 ? "..." : ""}`
    : "No session";

  return (
    <div className="shrink-0 border-b border-slate-200 px-4 py-3">
      <div className="flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-50 text-indigo-700">
            <Bot size={17} />
          </div>
          <div className="min-w-0">
            <h2 className="truncate text-sm font-semibold text-slate-950">
              Analysis chat
            </h2>
            <p className="truncate text-xs text-slate-500">{shortSessionId}</p>
          </div>
        </div>

        <div className="rounded-lg bg-slate-100 px-2.5 py-1.5 text-xs font-medium text-slate-600">
          {isStreaming ? "Streaming" : sessionId ? "Ready" : "Waiting"}
        </div>
      </div>
    </div>
  );
}
