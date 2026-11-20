import { Plus, ShieldCheck } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';

export function Header({ theme, onToggleTheme, onNewChat, backendStatus, hasMessages }) {
  const isConnected = backendStatus === 'connected';

  return (
    <header className="sticky top-0 z-20 backdrop-blur-md bg-white/85 dark:bg-slate-900/85 border-b border-slate-200 dark:border-slate-800 transition-colors">
      <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Left: Brand & Status */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white shadow-sm font-bold text-sm tracking-wide">
            HR
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-slate-900 dark:text-slate-100 leading-none">
                HR Policy Assistant
              </h1>
              <span className="hidden sm:inline-flex items-center gap-1 bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 text-[11px] font-medium px-2 py-0.5 rounded-full border border-indigo-200 dark:border-indigo-800/60">
                <ShieldCheck className="w-3 h-3 text-indigo-600 dark:text-indigo-400" />
                IIMA Policy Manual 2023
              </span>
            </div>
            <div className="flex items-center gap-1.5 mt-0.5 text-xs text-slate-500 dark:text-slate-400">
              <span
                className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-emerald-500 ring-2 ring-emerald-500/20' : 'bg-rose-500'
                }`}
              />
              <span className="text-[11px]">
                {isConnected ? 'Backend Online' : 'Backend Disconnected'}
              </span>
            </div>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          {hasMessages && (
            <button
              onClick={onNewChat}
              type="button"
              className="flex items-center gap-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 hover:text-indigo-600 dark:hover:text-indigo-400 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
              title="Start a new conversation"
            >
              <Plus className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">New Chat</span>
            </button>
          )}

          <ThemeToggle theme={theme} onToggle={onToggleTheme} />
        </div>
      </div>
    </header>
  );
}
