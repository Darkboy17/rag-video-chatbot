"use client";

import { KeyboardEvent, type SubmitEvent } from "react";
import { Send, Square } from "lucide-react";
import { SuggestedQuestions } from "./SuggestedQuestions";

/**
 * Props for the {@link ChatComposer} component.
 * input: A string representing the current input text.
 * isStreaming: A boolean indicating whether the chat is currently streaming.
 * isTextareaDisabled: A boolean indicating whether the textarea is disabled.
 * isSendDisabled: A boolean indicating whether the send button is disabled.
 * sessionId: A string representing the current chat session ID.
 * showSuggestions: A boolean indicating whether suggested questions are visible.
 * onInputChange: A function to update the input text.
 * onSendCurrentInput: A function to send the current input text.
 * onSelectSuggestedQuestion: A function to select a suggested question.
 * onShowSuggestionsChange: A function to update the visibility of suggested questions.
 * onStopStreaming: A function to stop the chat stream.
 */
type ChatComposerProps = {
  input: string;
  isStreaming: boolean;
  isTextareaDisabled: boolean;
  isSendDisabled: boolean;
  sessionId: string | null;
  showSuggestions: boolean;
  onInputChange: (value: string) => void;
  onSendCurrentInput: () => Promise<void>;
  onSelectSuggestedQuestion: (question: string) => Promise<void>;
  onShowSuggestionsChange: (value: boolean) => void;
  onStopStreaming: () => void;
};

/**
 * Bottom input area for chat messages, suggested prompts, and stream control.
 */
export function ChatComposer({
  input,
  isStreaming,
  isTextareaDisabled,
  isSendDisabled,
  sessionId,
  showSuggestions,
  onInputChange,
  onSendCurrentInput,
  onSelectSuggestedQuestion,
  onShowSuggestionsChange,
  onStopStreaming,
}: ChatComposerProps) {

  // Send the current input text when the form is submitted.
  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault(); // Prevent the form from submitting and reloading the page.
    await onSendCurrentInput();
  }

  async function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    // Enter submits like a chat app; Shift+Enter keeps multiline input.
    if (event.key !== "Enter" || event.shiftKey) {
      return;
    }

    event.preventDefault(); // Prevent the newline from being inserted into the textarea.
    await onSendCurrentInput(); // Send the current input text.
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="relative shrink-0 border-t border-slate-200 p-3"
    >
      {showSuggestions ? (
        <div className="absolute bottom-full left-1/2 z-20 mb-3 w-[min(92%,420px)] -translate-x-1/2">
          <SuggestedQuestions
            disabled={isStreaming}
            onSelect={onSelectSuggestedQuestion}
          />
        </div>
      ) : null}

      <div className="flex items-end gap-2 rounded-lg border border-slate-200 bg-slate-50 p-2 transition focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/10">
        <textarea
          value={input}
          disabled={isTextareaDisabled}
          onChange={(event) => onInputChange(event.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => onShowSuggestionsChange(true)}
          onBlur={() => onShowSuggestionsChange(false)}
          rows={1}
          placeholder={
            sessionId
              ? "Ask about hooks, retention, or engagement..."
              : "Analyze two videos first..."
          }
          className="max-h-28 min-h-9 min-w-0 flex-1 resize-none bg-transparent px-2 py-2 text-sm leading-5 outline-none disabled:text-slate-400"
        />

        {isStreaming ? (
          <button
            type="button"
            onClick={onStopStreaming}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-red-600 text-white transition hover:bg-red-500"
            aria-label="Stop streaming"
            title="Stop"
          >
            <Square size={15} />
          </button>
        ) : (
          <button
            type="submit"
            disabled={isSendDisabled}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-950 text-white transition hover:bg-slate-800 disabled:opacity-50"
            aria-label="Send message"
            title="Send"
          >
            <Send size={16} />
          </button>
        )}
      </div>
    </form>
  );
}
