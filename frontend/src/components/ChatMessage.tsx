import { useState } from "react";
import { PawPrint, FileText, ChevronDown } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Message } from "../hooks/useChat";
import type { Source } from "../api/client";

export default function ChatMessage({ role, content, sources }: Message) {
  const isAssistant = role === "assistant";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 260, damping: 20 }}
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
          <SourceList sources={sources} />
        )}
      </div>
    </motion.div>
  );
}

function SourceList({ sources }: { sources: Source[] }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.15 }}
      className="mt-2.5 space-y-1.5"
    >
      <span className="text-[11px] font-medium tracking-wide uppercase text-neutral-400 dark:text-neutral-500">
        Buddy fetched {sources.length} source{sources.length !== 1 ? "s" : ""}
      </span>
      {sources.map((src, i) => (
        <SourceCard key={i} source={src} index={i} />
      ))}
    </motion.div>
  );
}

function SourceCard({ source, index }: { source: Source; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const hasPreview = !!source.text_preview;
  const fileName = source.source_file ?? `chunk-${source.chunk_index}`;
  const scorePct = source.score != null ? Math.round(source.score * 100) : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 300, damping: 25, delay: 0.05 * index }}
      className="rounded-xl border border-neutral-200 dark:border-neutral-800
                 bg-white dark:bg-neutral-900/60
                 glow-hover hover:border-emerald-border transition-all"
    >
      <button
        onClick={() => hasPreview && setExpanded(!expanded)}
        disabled={!hasPreview}
        className={`w-full flex items-center gap-2.5 px-3 py-2 text-left
                    ${hasPreview ? "cursor-pointer" : "cursor-default"}`}
      >
        <FileText size={13} className="flex-shrink-0 text-emerald-deep dark:text-emerald-accent opacity-70" />

        <span className="flex-1 text-xs font-medium text-neutral-700 dark:text-neutral-300 truncate">
          {fileName}
        </span>

        {scorePct != null && (
          <span className="flex-shrink-0 text-[10px] tabular-nums font-medium
                           px-1.5 py-0.5 rounded-md
                           bg-emerald-50 dark:bg-emerald-950
                           text-emerald-deep dark:text-emerald-accent">
            {scorePct}%
          </span>
        )}

        {hasPreview && (
          <motion.span
            animate={{ rotate: expanded ? 180 : 0 }}
            transition={{ type: "spring", stiffness: 400, damping: 15 }}
            className="flex-shrink-0 text-neutral-400 dark:text-neutral-600"
          >
            <ChevronDown size={13} />
          </motion.span>
        )}
      </button>

      <AnimatePresence initial={false}>
        {expanded && hasPreview && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 28 }}
            className="overflow-hidden"
          >
            <div className="px-3 pb-2.5 pt-0">
              <div className="border-t border-neutral-100 dark:border-neutral-800 pt-2">
                <p className="text-[11px] leading-relaxed text-neutral-500 dark:text-neutral-400">
                  {source.text_preview}
                  {source.text_preview && source.text_preview.length >= 295 && (
                    <span className="text-neutral-400 dark:text-neutral-600">&hellip;</span>
                  )}
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
