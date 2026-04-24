import { useCallback, useEffect, useState } from "react";
import { PawPrint, X, RotateCcw } from "lucide-react";
import ConfirmDialog from "./components/ConfirmDialog";
import { motion, AnimatePresence } from "motion/react";
import { getInitialTheme, applyTheme } from "./api/theme";
import { useChat } from "./hooks/useChat";
import { useSync } from "./hooks/useSync";
import Header from "./components/Header";
import ChatMessage from "./components/ChatMessage";
import ChatInput from "./components/ChatInput";
import LoadingIndicator from "./components/LoadingIndicator";

export default function App() {
  const [theme, setTheme] = useState<"light" | "dark">(getInitialTheme);
  const [inputText, setInputText] = useState("");
  const [confirmOpen, setConfirmOpen] = useState(false);
  const { messages, isLoading, error, limitReached, sendMessage, clearError, clearChat, retry, bottomRef } = useChat();
  const { isSyncing, lastSync, syncError, clearSyncError, triggerSync } = useSync();

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((t) => (t === "light" ? "dark" : "light"));
  }, []);

  const handleSend = useCallback((text: string) => {
    sendMessage(text);
    setInputText("");
  }, [sendMessage]);

  const handleNewChat = useCallback(() => {
    if (messages.length === 0) return;
    setConfirmOpen(true);
  }, [messages.length]);

  const handleConfirmNewChat = useCallback(() => {
    clearChat();
    setInputText("");
    setConfirmOpen(false);
  }, [clearChat]);

  const isEmpty = messages.length === 0;

  return (
    <div className="min-h-screen flex flex-col">
      <Header
        theme={theme}
        onToggleTheme={toggleTheme}
        isSyncing={isSyncing}
        onSync={triggerSync}
        onNewChat={handleNewChat}
        lastSync={lastSync}
      />

      <main className="flex-1 overflow-y-auto px-4 pb-2">
        <div className="max-w-3xl mx-auto">
          <AnimatePresence>
            {syncError && (
              <ErrorBanner message={syncError} onDismiss={clearSyncError} />
            )}
          </AnimatePresence>

          {isEmpty && !isLoading ? (
            <EmptyState onSuggestionClick={setInputText} />
          ) : (
            <div className="py-6 space-y-5">
              {messages.map((msg, i) => (
                <ChatMessage key={i} {...msg} />
              ))}
              {isLoading && <LoadingIndicator />}
              <AnimatePresence>
                {error && (
                  <ErrorBanner
                    message={error}
                    onDismiss={clearError}
                    onRetry={!limitReached ? retry : undefined}
                  />
                )}
              </AnimatePresence>
              <div ref={bottomRef} />
            </div>
          )}
        </div>
      </main>

      <ChatInput
        text={inputText}
        onTextChange={setInputText}
        onSend={handleSend}
        disabled={limitReached || isLoading}
        limitReached={limitReached}
      />

      <ConfirmDialog
        open={confirmOpen}
        title="Start new chat?"
        message="This will clear the current conversation."
        confirmLabel="New Chat"
        onConfirm={handleConfirmNewChat}
        onCancel={() => setConfirmOpen(false)}
      />
    </div>
  );
}

function ErrorBanner({
  message,
  onDismiss,
  onRetry,
}: {
  message: string;
  onDismiss: () => void;
  onRetry?: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
      className="flex items-center gap-2 px-3 py-2 mt-3 rounded-lg text-sm
                 bg-red-50 dark:bg-red-950/40
                 text-red-700 dark:text-red-300
                 border border-red-200 dark:border-red-900"
    >
      <span className="flex-1">{message}</span>
      {onRetry && (
        <button onClick={onRetry} className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/50 transition-colors">
          <RotateCcw size={13} />
        </button>
      )}
      <button onClick={onDismiss} className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/50 transition-colors">
        <X size={13} />
      </button>
    </motion.div>
  );
}

function EmptyState({ onSuggestionClick }: { onSuggestionClick: (text: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <div className="w-16 h-16 rounded-full flex items-center justify-center
                      bg-emerald-50 dark:bg-emerald-950 mb-5">
        <PawPrint size={28} className="text-emerald-deep dark:text-emerald-accent" />
      </div>

      <h2 className="text-2xl font-semibold tracking-tight mb-2">
        Hey, I'm Buddy!
      </h2>
      <p className="text-neutral-500 dark:text-neutral-400 text-sm max-w-sm leading-relaxed">
        Your personal knowledge assistant. Ask me anything about your
        documents — I'll dig through everything and bring back what you need.
      </p>

      <div className="mt-6 flex flex-wrap justify-center gap-2">
        {[
          "What did my notes say about ",
          "Summarize the key points from ",
          "Find information about ",
        ].map((hint) => (
          <button
            key={hint}
            onClick={() => onSuggestionClick(hint)}
            className="px-3 py-1.5 text-xs rounded-full
                       bg-neutral-100 dark:bg-neutral-900
                       text-neutral-600 dark:text-neutral-400
                       border border-neutral-200 dark:border-neutral-800
                       glow-hover hover:border-emerald-border
                       hover:text-emerald-deep dark:hover:text-emerald-accent
                       active:scale-95 transition-all cursor-pointer"
          >
            {hint.trim()}...
          </button>
        ))}
      </div>
    </div>
  );
}
