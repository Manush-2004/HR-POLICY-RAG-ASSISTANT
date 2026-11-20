import { Bot, User, AlertCircle } from 'lucide-react';
import { FormattedText } from './FormattedText';
import { SourceCitations } from './SourceCitations';

export function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const isOutOfPolicy = message.role === 'assistant' && message.policy_found === false;

  return (
    <div
      className={`flex items-start gap-3 my-4 group ${
        isUser ? 'flex-row-reverse' : 'flex-row'
      } animate-fadeIn`}
    >
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center text-white flex-shrink-0 shadow-sm ${
          isUser
            ? 'bg-slate-700 dark:bg-slate-600'
            : isOutOfPolicy
            ? 'bg-gradient-to-tr from-amber-500 to-orange-500'
            : 'bg-gradient-to-tr from-indigo-600 to-violet-500'
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Bubble Container */}
      <div
        className={`max-w-[85%] md:max-w-[75%] rounded-2xl px-4 py-3 shadow-sm transition-all ${
          isUser
            ? 'bg-indigo-600 text-white rounded-tr-sm'
            : isOutOfPolicy
            ? 'bg-white dark:bg-slate-800 border border-amber-200 dark:border-amber-900/60 rounded-tl-sm'
            : 'bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700/80 rounded-tl-sm'
        }`}
      >
        {/* Out-of-policy banner badge */}
        {isOutOfPolicy && (
          <div className="flex items-center gap-1.5 text-xs font-medium text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-2 py-1 rounded-md mb-2 w-fit">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>Outside Document Scope</span>
          </div>
        )}

        {/* Content */}
        {isUser ? (
          <p className="text-white text-sm leading-relaxed whitespace-pre-wrap break-words">
            {message.content}
          </p>
        ) : (
          <div className="text-sm">
            <FormattedText content={message.content} />
            <SourceCitations sources={message.sources} />
          </div>
        )}

        {/* Timestamp */}
        {message.timestamp && (
          <div
            className={`text-[10px] mt-1.5 flex justify-end ${
              isUser ? 'text-indigo-200' : 'text-slate-400 dark:text-slate-500'
            }`}
          >
            {message.timestamp}
          </div>
        )}
      </div>
    </div>
  );
}
