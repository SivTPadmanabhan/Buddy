import { PawPrint } from "lucide-react";
import { motion } from "motion/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Message } from "../hooks/useChat";

export default function ChatMessage({ role, content, sources }: Message) {
  const isAssistant = role === "assistant";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
      className={`flex gap-3 ${isAssistant ? "" : "flex-row-reverse"}`}
    >
      {isAssistant && (
        <div className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center
                        bg-emerald-50 dark:bg-emerald-950 mt-1">
          <PawPrint size={14} className="text-emerald-deep dark:text-emerald-accent" />
        </div>
      )}

      <div className={`max-w-[85%] ${isAssistant ? "" : "ml-auto"}`}>
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed
            ${isAssistant
              ? "bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800"
              : "bg-emerald-deep dark:bg-emerald-accent text-white dark:text-black"
            }`}
        >
          {isAssistant ? (
            <div className="buddy-prose">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
            </div>
          ) : (
            <p className="whitespace-pre-wrap">{content}</p>
          )}
        </div>

        {sources && sources.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2">
            {sources.map((src, i) => (
              <motion.span
                key={i}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.1 * i }}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs
                           bg-neutral-100 dark:bg-neutral-800
                           text-neutral-500 dark:text-neutral-400
                           border border-transparent glow-hover
                           hover:border-emerald-border transition-colors cursor-default"
              >
                {src.source_file ?? `chunk-${src.chunk_index}`}
                {src.score != null && (
                  <span className="text-neutral-400 dark:text-neutral-500 tabular-nums">
                    {(src.score * 100).toFixed(0)}%
                  </span>
                )}
              </motion.span>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
