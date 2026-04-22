import { useCallback, useEffect, useState } from "react";
import { getInitialTheme, applyTheme } from "./api/theme";
import { useChat } from "./hooks/useChat";
import { useSync } from "./hooks/useSync";
import Header from "./components/Header";
import ChatMessage from "./components/ChatMessage";
import ChatInput from "./components/ChatInput";
import LoadingIndicator from "./components/LoadingIndicator";
import BuddyAnimation from "./components/BuddyAnimation";

export default function App() {
  const [theme, setTheme] = useState<"light" | "dark">(getInitialTheme);
  const { messages, isLoading, error, limitReached, sendMessage, bottomRef } = useChat();
  const { isSyncing, lastSync, triggerSync } = useSync();

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((t) => (t === "light" ? "dark" : "light"));
  }, []);

  const isEmpty = messages.length === 0;

  return (
    <div className="min-h-screen flex flex-col">
      <Header
        theme={theme}
        onToggleTheme={toggleTheme}
        isSyncing={isSyncing}
        onSync={triggerSync}
        lastSync={lastSync}
      />

      {/* Chat area */}
      <main className="flex-1 overflow-y-auto px-4 pb-2">
        <div className="max-w-3xl mx-auto">
          {isEmpty && !isLoading ? (
            <EmptyState />
          ) : (
            <div className="py-6 space-y-5">
              {messages.map((msg, i) => (
                <ChatMessage key={i} message={msg} index={i} />
              ))}
              {isLoading && <LoadingIndicator />}
              {error && (
                <div className="text-center text-sm text-red-500 dark:text-red-400 py-2">
                  {error}
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>
      </main>

      <ChatInput
        onSend={sendMessage}
        isLoading={isLoading}
        disabled={limitReached}
      />
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      {/* ============ EXPERIMENTAL: Animated JRT ============ */}
      <BuddyAnimation />
      {/* ============ END EXPERIMENTAL ============ */}

      <h2 className="font-display text-2xl font-bold text-emerald-dark dark:text-emerald-primary mt-6 mb-2">
        Hey, I'm Buddy!
      </h2>
      <p className="text-slate-500 dark:text-slate-400 text-sm max-w-sm leading-relaxed">
        Your personal knowledge assistant. Ask me to fetch answers from your
        documents — I'll dig through everything and bring back what you need.
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-2">
        {[
          "What did my notes say about...",
          "Summarize the key points from...",
          "Find information about...",
        ].map((hint) => (
          <span
            key={hint}
            className="px-3 py-1.5 text-xs rounded-full bg-emerald-primary/10
                       text-emerald-dark dark:text-emerald-primary border border-emerald-primary/20"
          >
            {hint}
          </span>
        ))}
      </div>
    </div>
  );
}
