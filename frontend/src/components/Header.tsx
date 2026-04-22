import { RefreshCw, Sun, Moon, BarChart3, PawPrint } from "lucide-react";
import { useState } from "react";
import type { UsageStatus } from "../api/client";
import { api } from "../api/client";

interface HeaderProps {
  theme: "light" | "dark";
  onToggleTheme: () => void;
  isSyncing: boolean;
  onSync: () => void;
  lastSync: string | null;
}

export default function Header({
  theme,
  onToggleTheme,
  isSyncing,
  onSync,
  lastSync,
}: HeaderProps) {
  const [usageOpen, setUsageOpen] = useState(false);
  const [usage, setUsage] = useState<UsageStatus | null>(null);

  const handleUsageClick = async () => {
    if (!usageOpen) {
      try {
        const data = await api.getUsage();
        setUsage(data);
      } catch {
        // ignore
      }
    }
    setUsageOpen(!usageOpen);
  };

  return (
    <header className="glass sticky top-0 z-50 px-4 py-3">
      <div className="max-w-3xl mx-auto flex items-center justify-between">
        {/* Logo & Name */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-primary/20 flex items-center justify-center">
            <PawPrint size={18} className="text-emerald-dark dark:text-emerald-primary" />
          </div>
          <h1 className="font-display text-xl font-bold tracking-tight text-emerald-dark dark:text-emerald-primary">
            Buddy
          </h1>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1.5">
          {/* Sync button */}
          <button
            onClick={onSync}
            disabled={isSyncing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium
                       text-slate-600 dark:text-slate-300 hover:bg-emerald-primary/10
                       transition-colors disabled:opacity-50"
            title={lastSync ? `Last sync: ${new Date(lastSync).toLocaleString()}` : "Never synced"}
          >
            <RefreshCw size={15} className={isSyncing ? "animate-spin" : ""} />
            <span className="hidden sm:inline">{isSyncing ? "Syncing..." : "Sync"}</span>
          </button>

          {/* Usage */}
          <div className="relative">
            <button
              onClick={handleUsageClick}
              className="p-2 rounded-lg text-slate-600 dark:text-slate-300
                         hover:bg-emerald-primary/10 transition-colors"
              title="Usage stats"
            >
              <BarChart3 size={16} />
            </button>

            {usageOpen && usage && (
              <div className="absolute right-0 top-full mt-2 w-64 glass rounded-xl p-4 shadow-lg z-50">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3">
                  Daily Usage
                </h3>
                <UsageBar label="Requests" entry={usage.gemini_requests} />
                <UsageBar label="Tokens" entry={usage.gemini_tokens} />
                <UsageBar label="Vectors" entry={usage.pinecone_vectors} />
              </div>
            )}
          </div>

          {/* Theme toggle */}
          <button
            onClick={onToggleTheme}
            className="p-2 rounded-lg text-slate-600 dark:text-slate-300
                       hover:bg-emerald-primary/10 transition-colors"
            title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
          >
            {theme === "light" ? <Moon size={16} /> : <Sun size={16} />}
          </button>
        </div>
      </div>
    </header>
  );
}

function UsageBar({ label, entry }: { label: string; entry: { used: number; limit: number; percent: number } }) {
  const pct = Math.min(entry.percent, 100);
  const barColor =
    pct >= 95 ? "bg-red-500" : pct >= 80 ? "bg-amber-500" : "bg-emerald-primary";

  return (
    <div className="mb-2.5 last:mb-0">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-slate-600 dark:text-slate-400">{label}</span>
        <span className="text-slate-500 dark:text-slate-500 tabular-nums">
          {entry.used.toLocaleString()} / {entry.limit.toLocaleString()}
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
