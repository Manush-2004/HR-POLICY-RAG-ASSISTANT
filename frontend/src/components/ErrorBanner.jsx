import { AlertCircle, RefreshCw } from 'lucide-react';

export function ErrorBanner({ message, onRetry }) {
  if (!message) return null;

  return (
    <div className="my-3 p-3.5 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 rounded-xl flex items-center justify-between text-sm text-rose-800 dark:text-rose-300 animate-fadeIn">
      <div className="flex items-center gap-2.5">
        <AlertCircle className="w-4 h-4 text-rose-600 dark:text-rose-400 flex-shrink-0" />
        <span className="text-xs sm:text-sm font-medium">{message}</span>
      </div>

      {onRetry && (
        <button
          onClick={onRetry}
          type="button"
          className="flex items-center gap-1 text-xs font-semibold px-2.5 py-1 bg-rose-100 dark:bg-rose-900/60 hover:bg-rose-200 dark:hover:bg-rose-800 text-rose-700 dark:text-rose-300 rounded-lg transition-colors cursor-pointer"
        >
          <RefreshCw className="w-3 h-3" />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
}
