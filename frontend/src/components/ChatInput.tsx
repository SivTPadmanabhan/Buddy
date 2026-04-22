import { type KeyboardEvent, useRef, useState } from "react";
import { Send } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  disabled: boolean;
}

export default function ChatInput({ onSend, isLoading, disabled }: ChatInputProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!text.trim() || isLoading || disabled) return;
    onSend(text);
    setText("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 150) + "px";
    }
  };

  return (
    <div className="sticky bottom-0 pb-4 pt-2 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="glass rounded-2xl px-4 py-3 flex items-end gap-3 shadow-lg shadow-emerald-primary/5">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            placeholder={
              disabled
                ? "Buddy is resting for today!"
                : "Ask Buddy to fetch something..."
            }
            disabled={disabled || isLoading}
            rows={1}
            className="flex-1 resize-none bg-transparent outline-none text-sm leading-relaxed
                       text-slate-800 dark:text-slate-100 placeholder:text-slate-400
                       dark:placeholder:text-slate-500 disabled:opacity-50"
          />

          <button
            onClick={handleSend}
            disabled={!text.trim() || isLoading || disabled}
            className="flex-shrink-0 w-8 h-8 rounded-xl bg-emerald-primary text-white
                       flex items-center justify-center transition-all
                       hover:bg-emerald-dark disabled:opacity-30 disabled:hover:bg-emerald-primary"
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Send size={15} />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
