import { Calendar, ShieldAlert, Award, Stethoscope, ArrowRight, Sparkles } from 'lucide-react';

const SUGGESTED_TOPICS = [
  {
    icon: Calendar,
    title: 'Leave & Attendance',
    query: 'What are the rules and entitlements for casual leave and earned leave?',
  },
  {
    icon: Award,
    title: 'Probation & Confirmation',
    query: 'What are the policies regarding employee probation period and confirmation?',
  },
  {
    icon: Stethoscope,
    title: 'Medical & Healthcare',
    query: 'What are the medical examination and health reimbursement policies for employees?',
  },
  {
    icon: ShieldAlert,
    title: 'Conduct & Ethics',
    query: 'What are the institute conduct rules, ethics, and disciplinary guidelines?',
  },
];

export function EmptyState({ onSelectTopic }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 max-w-2xl mx-auto text-center animate-fadeIn">
      <div className="w-14 h-14 rounded-2xl bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-100 dark:border-indigo-800 flex items-center justify-center text-indigo-600 dark:text-indigo-400 mb-4 shadow-sm">
        <Sparkles className="w-7 h-7" />
      </div>

      <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-100 tracking-tight">
        Welcome to HR Policy Assistant
      </h2>
      <p className="text-slate-600 dark:text-slate-400 text-sm mt-2 max-w-md">
        Ask any question about institute employment terms, leave entitlements, benefits, appraisals, and official procedures.
      </p>

      <div className="w-full grid grid-cols-1 sm:grid-cols-2 gap-3 mt-8">
        {SUGGESTED_TOPICS.map((topic, idx) => {
          const Icon = topic.icon;
          return (
            <button
              key={idx}
              type="button"
              onClick={() => onSelectTopic(topic.query)}
              className="flex flex-col text-left p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/80 hover:border-indigo-500 dark:hover:border-indigo-500 hover:shadow-md transition-all group cursor-pointer"
            >
              <div className="flex items-center justify-between w-full mb-1.5">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 group-hover:scale-105 transition-transform">
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                    {topic.title}
                  </span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-500 group-hover:translate-x-0.5 transition-all" />
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 leading-relaxed">
                "{topic.query}"
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
