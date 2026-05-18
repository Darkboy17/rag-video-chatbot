/**
 * Props for the {@link ChatEmptyState} component.
 * sessionId: A string representing the current chat session ID.
 */
type ChatEmptyStateProps = {
  sessionId: string | null;
};

/**
 * Placeholder state for the chat panel before any messages are shown.
 */
export function ChatEmptyState({ sessionId }: ChatEmptyStateProps) {
  return (
    <div className="flex h-full min-h-70 items-center justify-center text-center">
      <div>
        <p className="text-sm font-semibold text-slate-950">
          {sessionId ? "Ready for questions" : "Analyze two videos first"}
        </p>
        <p className="mt-1 text-xs text-slate-500">
          {sessionId ? "Sources will appear with answers." : "Chat unlocks after indexing."}
        </p>
      </div>
    </div>
  );
}
