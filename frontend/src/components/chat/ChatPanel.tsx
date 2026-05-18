"use client";


import type { ChatMessage as ChatMessageType } from "@/types/api";
import { useHasHydrated } from "@/hooks/useHasHydrated";
import { useEffect, useRef, useState } from "react";
import { ChatEmptyState } from "./ChatEmptyState";
import { ChatComposer } from "./ChatComposer";
import { ChatMessage } from "./ChatMessage";
import { ChatHeader } from "./ChatHeader";

/**
 * Props for the {@link ChatPanel} component.
 * sessionId: A string representing the current chat session ID.
 * messages: An array of chat messages.
 * isStreaming: A boolean indicating whether the chat is currently streaming.
 * error: A string representing the error message, if any.
 * onSendMessage: A function to send a message.
 * onStopStreaming: A function to stop the chat stream.
 */
type ChatPanelProps = {
  sessionId: string | null;
  messages: ChatMessageType[];
  isStreaming: boolean;
  error: string | null;
  onSendMessage: (message: string) => Promise<void>;
  onStopStreaming: () => void;
};

/**
 * Owns chat panel state that is purely presentational: input text, suggestion
 * visibility, and scroll anchoring. Network state stays in useStreamingChat.
 */
export function ChatPanel({
  sessionId,
  messages,
  isStreaming,
  error,
  onSendMessage,
  onStopStreaming,
}: ChatPanelProps) {

  // The input text for the chat composer. 
  const [input, setInput] = useState("");

  // The visibility of suggested questions.
  const [showSuggestions, setShowSuggestions] = useState(false);

  // The hydration guard prevents the disabled state from changing between the
  // server-rendered shell and the first client render.
  const hasMounted = useHasHydrated();

  // The anchor for scrolling to the bottom of the message list.
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // The disabled state for the chat composer.
  const isDisabled = !sessionId || isStreaming;

  // The hydration guard prevents the disabled state from changing between the
  // server-rendered shell and the first client render.
  const isTextareaDisabled = hasMounted && !sessionId;
  const isSendDisabled = hasMounted && (isDisabled || !input.trim());
  const shouldShowSuggestions = Boolean(sessionId && showSuggestions && !isStreaming);

  // Scroll to the bottom of the message list when new messages arrive.
  useEffect(() => {
    if (messages.length === 0) {
      return;
    }

    // During streaming, use instant scrolling so token-by-token updates stay
    // anchored without running a smooth animation for every token.
    messagesEndRef.current?.scrollIntoView({
      behavior: isStreaming ? "auto" : "smooth",
      block: "end",
    });
  }, [messages, isStreaming]);

  /**
   * Send the current input text when the form is submitted.
   * @returns A promise that resolves when the message is sent.
   */
  async function sendCurrentInput() {
    const value = input.trim();

    if (!value) {
      return;
    }

    setInput("");
    setShowSuggestions(false);
    await onSendMessage(value);
  }

  /**
   * Send a suggested question.
   * @param question The question to send.
   * @returns A promise that resolves when the message is sent.
   */
  async function handleSuggestedQuestion(question: string) {
    setInput("");
    setShowSuggestions(false);
    await onSendMessage(question);
  }

  return (
    <section className="flex h-full min-h-0 flex-col rounded-lg border border-slate-200 bg-white shadow-sm">
      <ChatHeader sessionId={sessionId} isStreaming={isStreaming} />

      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 py-4">
        {messages.length === 0 ? (
          <ChatEmptyState sessionId={sessionId} />
        ) : (
          messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {error ? (
        <div className="mx-4 mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <ChatComposer
        input={input}
        isStreaming={isStreaming}
        isTextareaDisabled={isTextareaDisabled}
        isSendDisabled={isSendDisabled}
        sessionId={sessionId}
        showSuggestions={shouldShowSuggestions}
        onInputChange={setInput}
        onSendCurrentInput={sendCurrentInput}
        onSelectSuggestedQuestion={handleSuggestedQuestion}
        onShowSuggestionsChange={setShowSuggestions}
        onStopStreaming={onStopStreaming}
      />
    </section>
  );
}