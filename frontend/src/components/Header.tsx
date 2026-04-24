import { RefreshCw, Sun, Moon, BarChart3, PawPrint, SquarePen } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import type { UsageStatus } from "../api/client";
import { api } from "../api/client";

interface HeaderProps {
  theme: "light" | "dark";
  onToggleTheme: () => void;
  isSyncing: boolean;
  onSync: () => void;
  onNewChat: () => void;
  lastSync: string | null;
}

export default function Header({ theme, onToggleTheme, isSyncing, onSync, onNewChat, lastSync }: HeaderProps) {
  const [usageOpen, setUsageOpen] = useState(false);
  const [usage, setUsage] = useState<UsageStatus | null>(null);
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!usageOpen) return;
    const handleClick = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setUsageOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [usageOpen]);

  const handleUsageClick = async () => {
    if (!usageOpen) {
      try { setUsage(await api.getUsage()); } catch { /* ignore */ }
    }
    setUsageOpen(!usageOpen);
  };

  return (
    <header className="sticky top-0 z-50 border-b border-neutral-200 dark:border-neutral-800 bg-white dark:bg-black">
      <div className="max-w-3xl mx-auto flex items-center justify-between px-4 h-14">
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={onNewChat}
            className="flex items-center gap-2.5 px-1 py-1 -ml-1 rounded-lg
                       glow-hover hover:border-emerald-border
                       border border-transparent transition-colors cursor-pointer"
            title="New chat"
          >
            <PawPrint size={20} className="text-emerald-deep dark:text-emerald-accent" />
            <span className="text-lg font-semibold tracking-tight">Buddy</span>
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onNewChat}
            className="p-2 rounded-lg text-neutral-600 dark:text-neutral-400
                       border border-transparent glow-hover
                       hover:border-emerald-border transition-colors"
            title="New chat"
          >
            <SquarePen size={15} />
          </motion.button>
        </div>

        <div className="flex items-center gap-1">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onSync}
            disabled={isSyncing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm
                       text-neutral-600 dark:text-neutral-400
                       border border-transparent glow-hover
                       hover:border-emerald-border
                       disabled:opacity-40 transition-colors"
            title={lastSync ? `Last sync: ${new Date(lastSync).toLocaleString()}` : "Never synced"}
          >
            <RefreshCw size={14} className={isSyncing ? "animate-spin" : ""} />
            <span className="hidden sm:inline">{isSyncing ? "Syncing" : "Sync"}</span>
          </motion.button>

          <div className="relative" ref={popoverRef}>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleUsageClick}
              className="p-2 rounded-lg text-neutral-600 dark:text-neutral-400
                         border border-transparent glow-hover
                         hover:border-emerald-border transition-colors"
            >
              <BarChart3 size={15} />
            </motion.button>

            <AnimatePresence>
              {usageOpen && usage && (
                <motion.div
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  transition={{ type: "spring", stiffness: 400, damping: 25 }}
                  className="absolute right-0 top-full mt-2 w-60 rounded-xl p-4 shadow-lg
                             bg-white dark:bg-neutral-900
                             border border-neutral-200 dark:border-neutral-800 z-50"
                >
                  <h3 className="text-xs font-medium uppercase tracking-wider text-neutral-500 mb-3">
                    Daily Usage
                  </h3>
                  <UsageBar label="Requests" entry={usage.gemini_requests} />
                  <UsageBar label="Tokens" entry={usage.gemini_tokens} />
                  <UsageBar label="Vectors" entry={usage.pinecone_vectors} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onToggleTheme}
            className="p-2 rounded-lg text-neutral-600 dark:text-neutral-400
                       border border-transparent glow-hover
                       hover:border-emerald-border transition-colors"
          >
            {theme === "light" ? <Moon size={15} /> : <Sun size={15} />}
          </motion.button>
        </div>
      </div>
    </header>
  );
}

function UsageBar({ label, entry }: { label: string; entry: { used: number; limit: number; percent: number } }) {
  const pct = Math.min(entry.percent, 100);
  const color = pct >= 95 ? "bg-red-500" : pct >= 80 ? "bg-amber-500" : "bg-emerald-deep dark:bg-emerald-accent";

  return (
    <div className="mb-3 last:mb-0">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-neutral-600 dark:text-neutral-400">{label}</span>
        <span className="text-neutral-500 tabular-nums">
          {entry.used.toLocaleString()} / {entry.limit.toLocaleString()}
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-neutral-100 dark:bg-neutral-800 overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-500 ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
