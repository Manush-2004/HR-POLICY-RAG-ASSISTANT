import { useState, useEffect, useRef } from 'react';
import { useChat } from './hooks/useChat';
import { Header } from './components/Header';
import { EmptyState } from './components/EmptyState';
import { MessageBubble } from './components/MessageBubble';
import { TypingIndicator } from './components/TypingIndicator';
import { ChatInput } from './components/ChatInput';
import { ErrorBanner } from './components/ErrorBanner';

function App() {
  // Theme state persisted in localStorage
  const [theme, setTheme] = useState(() => {
    try {
      const saved = localStorage.getItem('hr_assistant_theme');
      if (saved) return saved;
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    } catch {
      return 'light';
    }
  });

  const {
    messages,
    isLoading,
    error,
    backendState,
    sendMessage,
    clearChat,
    retryHealth,
  } = useChat();

  const messagesEndRef = useRef(null);

  // Apply theme class to document
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    try {
      localStorage.setItem('hr_assistant_theme', theme);
    } catch {
      // ignore
    }
  }, [theme]);

  // Smooth scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const isDisconnected = backendState.status === 'disconnected';

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 transition-colors">
      {/* Top Header */}
      <Header
        theme={theme}
        onToggleTheme={toggleTheme}
        onNewChat={clearChat}
        backendStatus={backendState.status}
        hasMessages={messages.length > 0}
      />

      {/* Main Chat Area */}
      <main className="flex-1 max-w-4xl w-full mx-auto px-4 flex flex-col">
        {/* Backend disconnected alert banner */}
        {isDisconnected && (
          <div className="mt-3">
            <ErrorBanner
              message="Cannot connect to the backend server at http://localhost:8000. Please ensure the FastAPI server is running."
              onRetry={retryHealth}
            />
          </div>
        )}

        {/* Dynamic chat content or empty state */}
        <div className="flex-1 py-4">
          {messages.length === 0 ? (
            <EmptyState onSelectTopic={sendMessage} />
          ) : (
            <div className="space-y-1">
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}

              {isLoading && <TypingIndicator />}

              {error && <ErrorBanner message={error} />}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Bottom Input Area */}
        <div className="sticky bottom-0 pb-4 pt-2 bg-gradient-to-t from-slate-50 via-slate-50/90 to-transparent dark:from-slate-900 dark:via-slate-900/90 dark:to-transparent">
          <ChatInput
            onSendMessage={sendMessage}
            isLoading={isLoading}
            disabled={isDisconnected}
          />
          <p className="text-[11px] text-center text-slate-400 dark:text-slate-500 mt-2 select-none">
            Answers are grounded in the IIMA HR Policy Manual (2023). For binding decisions, consult the HR Department.
          </p>
        </div>
      </main>
    </div>
  );
}

export default App;
