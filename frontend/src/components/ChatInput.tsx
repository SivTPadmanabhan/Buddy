import { Send } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { motion } from "motion/react";

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [text]);

  const handleSubmit = () => {
    if (!text.trim() || disabled) return;
    onSend(text);
    setText("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-neutral-200 dark:border-neutral-800 bg-white dark:bg-black">
      <div className="max-w-3xl mx-auto px-4 py-3">
        <div className="flex items-end gap-2 rounded-xl border border-neutral-200 dark:border-neutral-800
                        bg-neutral-50 dark:bg-neutral-900 px-3 py-2
                        glow-focus focus-within:border-emerald-border transition-all">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask Buddy anything..."
            disabled={disabled}
            rows={1}
            className="flex-1 resize-none bg-transparent text-sm leading-relaxed
                       placeholder:text-neutral-400 dark:placeholder:text-neutral-600
                       focus:outline-none disabled:opacity-40"
          />
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={handleSubmit}
            disabled={disabled || !text.trim()}
            className={`flex-shrink-0 p-2 rounded-lg transition-all
              ${text.trim() && !disabled
                ? "bg-emerald-deep dark:bg-emerald-accent text-white dark:text-black emerald-pulse"
                : "text-neutral-300 dark:text-neutral-700"
              } disabled:opacity-40`}
          >
            <Send size={16} />
          </motion.button>
        </div>
      </div>
    </div>
  );
}
