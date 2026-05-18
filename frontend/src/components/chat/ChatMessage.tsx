import type { ChatMessage as ChatMessageType } from "@/types/api";
import { MessageMarkdown } from "./MessageMarkdown";
import { TypingIndicator } from "./TypingIndicator";
import { SourceList } from "./SourceList";
import clsx from "clsx";

/**
 * Props for {@link ChatMessage}.
 * message: The chat message to render.
 */
type ChatMessageProps = {
  message: ChatMessageType;
};

/**
 * Renders one chat bubble, switching between user text, assistant markdown,
 * and the streaming placeholder.
 */
export function ChatMessage({ message }: ChatMessageProps) {

  // Check if the message is from the user
  const isUser = message.role === "user";

  // Get the message content
  const content = message.content;

  // Check if the message is waiting for the assistant
  const isWaitingForAssistant = !isUser && !content;

  return (
    <div
      className={clsx(
        "flex",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={clsx(
          "max-w-[86%] rounded-lg px-3.5 py-2.5 text-sm leading-6",
          isUser
            ? "bg-slate-950 text-white"
            : "bg-slate-50 text-slate-800"
        )}
      >
        {isUser ? (
          <div className="whitespace-pre-wrap">{content}</div>
        ) : isWaitingForAssistant ? (
          <TypingIndicator />
        ) : (
          <div className="min-w-0">
            <MessageMarkdown content={content} />
          </div>
        )}

        {!isUser && message.sources ? (
          <SourceList sources={message.sources} />
        ) : null}
      </div>
    </div>
  );
}
