import { motion } from "motion/react";
import { PawPrint } from "lucide-react";

export default function LoadingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-3"
    >
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-emerald-primary/15 flex items-center justify-center">
        <PawPrint size={16} className="text-emerald-dark dark:text-emerald-primary" />
      </div>
      <div className="bg-white dark:bg-surface-card-dark border border-slate-100 dark:border-slate-700/50 rounded-2xl px-4 py-3 shadow-sm">
        <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
          <motion.span
            animate={{ opacity: [0.4, 1, 0.4] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          >
            Fetching
          </motion.span>
          <span className="flex gap-0.5">
            {[0, 1, 2].map((i) => (
              <motion.span
                key={i}
                animate={{ opacity: [0.2, 1, 0.2] }}
                transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
              >
                .
              </motion.span>
            ))}
          </span>
        </div>
      </div>
    </motion.div>
  );
}
