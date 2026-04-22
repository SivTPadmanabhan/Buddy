import { useCallback, useRef, useState } from "react";
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

  const scrollToBottom = useCallback(() => {
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isLoading) return;

      setError(null);
      const updated = [...messages, { role: "user" as const, content: trimmed }];
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
    [isLoading, messages, scrollToBottom],
  );

  return { messages, isLoading, error, limitReached, sendMessage, bottomRef };
}
