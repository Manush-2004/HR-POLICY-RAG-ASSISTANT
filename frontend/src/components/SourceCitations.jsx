import { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, FileText } from 'lucide-react';

export function SourceCitations({ sources }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700/60 text-xs">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 font-medium py-1 transition-colors"
      >
        <div className="flex items-center gap-1.5">
          <BookOpen className="w-3.5 h-3.5" />
          <span>
            {sources.length} Policy Source Citation{sources.length > 1 ? 's' : ''}
          </span>
        </div>
        {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
      </button>

      {isOpen && (
        <div className="mt-2 space-y-2 animate-fadeIn">
          {sources.map((item, idx) => (
            <div
              key={idx}
              className="bg-slate-50 dark:bg-slate-800/80 rounded-md p-2.5 border border-slate-200/80 dark:border-slate-700/70"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-slate-700 dark:text-slate-200 flex items-center gap-1">
                  <FileText className="w-3 h-3 text-indigo-500" />
                  {item.source}
                </span>
                <span className="bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 px-1.5 py-0.5 rounded text-[11px] font-medium">
                  Page {item.page}
                </span>
              </div>
              <p className="text-slate-600 dark:text-slate-300 italic line-clamp-3 leading-relaxed">
                "{item.snippet}"
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
