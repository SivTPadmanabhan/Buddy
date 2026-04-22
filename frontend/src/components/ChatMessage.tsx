import { useState } from "react";
import { motion } from "motion/react";
import { ChevronDown, ChevronRight, PawPrint, FileText } from "lucide-react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Message } from "../hooks/useChat";

interface ChatMessageProps {
  message: Message;
  index: number;
}

export default function ChatMessage({ message, index }: ChatMessageProps) {
  const isAssistant = message.role === "assistant";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className={`flex gap-3 ${isAssistant ? "" : "flex-row-reverse"}`}
    >
      {/* Avatar */}
      {isAssistant && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-emerald-primary/15 flex items-center justify-center mt-1">
          <PawPrint size={16} className="text-emerald-dark dark:text-emerald-primary" />
        </div>
      )}

      {/* Bubble */}
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isAssistant
            ? "bg-white dark:bg-surface-card-dark border border-slate-100 dark:border-slate-700/50 shadow-sm"
            : "bg-emerald-primary text-white shadow-md shadow-emerald-primary/20"
        }`}
      >
        {isAssistant ? (
          <div className="buddy-prose text-sm text-slate-700 dark:text-slate-200 leading-relaxed">
            <Markdown remarkPlugins={[remarkGfm]}>{message.content}</Markdown>
          </div>
        ) : (
          <p className="text-sm leading-relaxed">{message.content}</p>
        )}

        {/* Sources */}
        {isAssistant && message.sources && message.sources.length > 0 && (
          <SourcesAccordion sources={message.sources} />
        )}
      </div>
    </motion.div>
  );
}

function SourcesAccordion({
  sources,
}: {
  sources: NonNullable<Message["sources"]>;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="mt-2.5 pt-2.5 border-t border-slate-100 dark:border-slate-700/50">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-xs font-medium text-emerald-dark dark:text-emerald-primary hover:underline"
      >
        {open ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
        Buddy found {sources.length} source{sources.length !== 1 ? "s" : ""}
      </button>

      {open && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          transition={{ duration: 0.2 }}
          className="mt-2 space-y-1.5"
        >
          {sources.map((s, i) => (
            <div
              key={i}
              className="glass rounded-lg px-3 py-2 flex items-center gap-2 text-xs"
            >
              <FileText size={13} className="text-emerald-dark dark:text-emerald-primary flex-shrink-0" />
              <span className="text-slate-600 dark:text-slate-300 truncate">
                {s.source_file || "Unknown"}
              </span>
              {s.score != null && (
                <span className="ml-auto text-slate-400 tabular-nums">
                  {(s.score * 100).toFixed(0)}%
                </span>
              )}
            </div>
          ))}
        </motion.div>
      )}
    </div>
  );
}
