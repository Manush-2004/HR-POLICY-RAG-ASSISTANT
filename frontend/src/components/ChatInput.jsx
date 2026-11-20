import { useState, useRef, useEffect } from 'react';
import { Send, CornerDownLeft } from 'lucide-react';

export function ChatInput({ onSendMessage, isLoading, disabled }) {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 140)}px`;
    }
  }, [input]);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading || disabled) return;
    onSendMessage(input);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="relative flex items-end gap-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-2xl p-2 shadow-sm focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 transition-all"
    >
      <textarea
        ref={textareaRef}
        rows={1}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={
          disabled
            ? 'Backend disconnected. Please start the FastAPI server...'
            : 'Ask a question about HR policies (e.g., leave, medical benefits, probation)...'
        }
        disabled={disabled || isLoading}
        className="flex-1 max-h-36 resize-none bg-transparent px-3 py-1.5 text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none leading-relaxed disabled:opacity-50"
      />

      <div className="flex items-center gap-1.5 pb-0.5 pr-1">
        <span className="hidden sm:inline-flex items-center text-[10px] text-slate-400 dark:text-slate-500 select-none">
          <CornerDownLeft className="w-3 h-3 mr-0.5" /> Enter
        </span>

        <button
          type="submit"
          disabled={!input.trim() || isLoading || disabled}
          className="w-9 h-9 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-200 dark:disabled:bg-slate-700 text-white disabled:text-slate-400 flex items-center justify-center transition-all cursor-pointer disabled:cursor-not-allowed shadow-sm"
          title="Send question"
          aria-label="Send message"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </form>
  );
}
