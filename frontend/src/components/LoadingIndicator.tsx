import { PawPrint } from "lucide-react";
import { motion } from "motion/react";

export default function LoadingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-3"
    >
      <div className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center
                      bg-emerald-50 dark:bg-emerald-950 mt-1">
        <PawPrint size={14} className="text-emerald-deep dark:text-emerald-accent" />
      </div>

      <div className="flex items-center gap-1.5 px-4 py-3 rounded-2xl
                      bg-neutral-50 dark:bg-neutral-900
                      border border-neutral-200 dark:border-neutral-800">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="w-1.5 h-1.5 rounded-full bg-emerald-deep dark:bg-emerald-accent"
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
          />
        ))}
      </div>
    </motion.div>
  );
}
