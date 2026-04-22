import { useCallback, useEffect, useState } from "react";
import { PawPrint } from "lucide-react";
import { getInitialTheme, applyTheme } from "./api/theme";
import { useChat } from "./hooks/useChat";
import { useSync } from "./hooks/useSync";
import Header from "./components/Header";
import ChatMessage from "./components/ChatMessage";
import ChatInput from "./components/ChatInput";
import LoadingIndicator from "./components/LoadingIndicator";

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

      <main className="flex-1 overflow-y-auto px-4 pb-2">
        <div className="max-w-3xl mx-auto">
          {isEmpty && !isLoading ? (
            <EmptyState />
          ) : (
            <div className="py-6 space-y-5">
              {messages.map((msg, i) => (
                <ChatMessage key={i} {...msg} />
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

      <ChatInput onSend={sendMessage} disabled={limitReached || isLoading} />
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <div className="w-16 h-16 rounded-full flex items-center justify-center
                      bg-emerald-50 dark:bg-emerald-950 mb-5">
        <PawPrint size={28} className="text-emerald-deep dark:text-emerald-accent" />
      </div>

      <h2 className="text-2xl font-semibold tracking-tight mb-2">
        Hey, I'm Buddy!
      </h2>
      <p className="text-neutral-500 text-sm max-w-sm leading-relaxed">
        Your personal knowledge assistant. Ask me anything about your
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
            className="px-3 py-1.5 text-xs rounded-full
                       bg-neutral-100 dark:bg-neutral-900
                       text-neutral-500 dark:text-neutral-400
                       border border-neutral-200 dark:border-neutral-800
                       glow-hover hover:border-emerald-border transition-colors cursor-default"
          >
            {hint}
          </span>
        ))}
      </div>
    </div>
  );
}
