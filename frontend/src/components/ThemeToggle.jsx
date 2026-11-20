import { Sun, Moon } from 'lucide-react';

export function ThemeToggle({ theme, onToggle }) {
  const isDark = theme === 'dark';

  return (
    <button
      onClick={onToggle}
      type="button"
      className="p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors"
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      aria-label="Toggle theme"
    >
      {isDark ? (
        <Sun className="w-5 h-5 text-amber-400 hover:rotate-45 transition-transform" />
      ) : (
        <Moon className="w-5 h-5 text-slate-700 hover:-rotate-12 transition-transform" />
      )}
    </button>
  );
}
