"use client";


import { getChatStreamResponse } from "@/lib/api";
import type { ChatMessage } from "@/types/api";
import { readSseStream } from "@/lib/sse";
import { useRef, useState } from "react";


/**
 * Creates a unique ID for a chat message.
 * @returns A string representing the message ID.
 */
function createMessageId(): string {
  return crypto.randomUUID();
}

/**
 * Pauses the current task for the next paint cycle.
 * @returns A promise that resolves after the next paint cycle.
 */
function waitForNextPaint(): Promise<void> {
  // Yield after each streamed token so React can paint long answers smoothly.
  return new Promise((resolve) => {
    requestAnimationFrame(() => resolve());
  });
}

/**
 * Manages the chat SSE lifecycle for one analysis session.
 */
export function useStreamingChat(sessionId: string | null) {

  // The chat history.
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  // The current state of the chat stream.
  const [isStreaming, setIsStreaming] = useState(false);

  // The error message, if any.
  const [error, setError] = useState<string | null>(null);

  // The abort controller for the current chat stream.
  const abortControllerRef = useRef<AbortController | null>(null);

  /**
   * Sends a message to the chat stream.
   * @param content The content of the message.
   */
  async function sendMessage(content: string) {

    // Don't start a new stream if one is already in progress.
    if (!sessionId) {
      setError("Analyze two videos first before chatting.");
      return;
    }

    // Get rid of leading and trailing whitespace.
    const trimmed = content.trim();

    // Don't start a new stream if the user hasn't typed anything.
    if (!trimmed || isStreaming) {
      return;
    }

    // set error to null
    setError(null);

    // set isStreaming to true
    setIsStreaming(true);

    // Add the user's message to the chat history.
    const userMessage: ChatMessage = {
      id: createMessageId(),
      role: "user",
      content: trimmed,
    };

    // Create a unique ID for the assistant message.
    const assistantMessageId = createMessageId();

    // Insert an empty assistant message immediately so the UI can show the
    // typing indicator while the backend prepares the first streamed token.
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      sources: [],
    };

    // Add the user and assistant messages to the chat history.
    setMessages((current) => [...current, userMessage, assistantMessage]);

    // Create an abort controller for the current chat stream.
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const response = await getChatStreamResponse(
        sessionId,
        trimmed,
        abortController.signal
      );

      // Read the chat stream and update the chat history.
      await readSseStream(response, {
        async onToken(token) {

          // Tokens arrive incrementally; append them to the placeholder message
          // instead of replacing the whole chat history.
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantMessageId
                ? {
                  ...message,
                  content: message.content + token,
                }
                : message
            )
          );

          await waitForNextPaint();
        },

        onSources(event) {
          const sources = event.data.sources;

          // Sources arrive after the answer text so citations attach to the
          // assistant bubble without interrupting the token stream.
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantMessageId
                ? {
                  ...message,
                  sources,
                }
                : message
            )
          );
        },

        onError(message) {
          setError(message);
        },

        onDone() {
          setIsStreaming(false);
        },
      });
    } catch (error) {

      // Set the error message.
      const message =
        error instanceof Error
          ? error.message
          : "Something went wrong while streaming the answer.";

      // Set the error message if it's not an abort error.
      if (message !== "The operation was aborted.") {
        setError(message);
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  }

  /**
   * Stops the current chat stream.
   * @returns A promise that resolves when the stream is stopped.
   */
  function stopStreaming() {
    abortControllerRef.current?.abort();
    setIsStreaming(false);
  }

  /**
   * Clears the chat history.
   * @returns null.
   */
  function clearMessages() {
    setMessages([]);
    setError(null);
  }

  return {
    messages,
    isStreaming,
    error,
    sendMessage,
    stopStreaming,
    clearMessages,
  };
}