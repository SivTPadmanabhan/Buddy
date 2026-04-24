import { useCallback, useEffect, useRef, useState } from "react";
import { api, type Source, BuddyApiError } from "../api/client";

export interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [limitReached, setLimitReached] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const messagesRef = useRef(messages);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  const scrollToBottom = useCallback(() => {
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
    setLimitReached(false);
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isLoading) return;

      setError(null);
      const updated = [...messagesRef.current, { role: "user" as const, content: trimmed }];
      setMessages(updated);
      setIsLoading(true);
      scrollToBottom();

      try {
        const recent = updated.slice(-10).map((m) => ({ role: m.role, content: m.content }));
        const res = await api.chat(trimmed, recent);
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: res.response, sources: res.sources },
        ]);
      } catch (e) {
        if (e instanceof BuddyApiError && e.limitReached) {
          setLimitReached(true);
          setError("Buddy is resting for today! Daily limit reached.");
        } else if (e instanceof Error) {
          setError(e.message);
        } else {
          setError("Something went wrong.");
        }
      } finally {
        setIsLoading(false);
        scrollToBottom();
      }
    },
    [isLoading, scrollToBottom],
  );

  const retry = useCallback(() => {
    const lastUserMsg = [...messagesRef.current].reverse().find((m) => m.role === "user");
    if (!lastUserMsg) return;
    setMessages((prev) => prev.slice(0, -1));
    sendMessage(lastUserMsg.content);
  }, [sendMessage]);

  return { messages, isLoading, error, limitReached, sendMessage, clearError, clearChat, retry, bottomRef };
}
