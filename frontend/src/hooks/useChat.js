import { useState, useEffect, useCallback } from 'react';
import { fetchHealth, sendChatMessage } from '../services/api';

const STORAGE_KEY = 'hr_assistant_messages';

export function useChat() {
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [backendState, setBackendState] = useState({
    status: 'checking', // 'checking' | 'connected' | 'disconnected'
    details: null,
  });

  // Save messages to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    } catch {
      // ignore storage quota issues
    }
  }, [messages]);

  // Periodic health check using mounted subscription pattern
  const checkHealth = useCallback(async () => {
    try {
      const data = await fetchHealth();
      setBackendState({
        status: data.status === 'ok' ? 'connected' : 'connected',
        details: data,
      });
      setError(null);
    } catch {
      setBackendState({
        status: 'disconnected',
        details: null,
      });
    }
  }, []);

  useEffect(() => {
    let isMounted = true;

    const poll = async () => {
      try {
        const data = await fetchHealth();
        if (isMounted) {
          setBackendState({
            status: data.status === 'ok' ? 'connected' : 'connected',
            details: data,
          });
          setError(null);
        }
      } catch {
        if (isMounted) {
          setBackendState({
            status: 'disconnected',
            details: null,
          });
        }
      }
    };

    poll();
    const interval = setInterval(poll, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const sendMessage = useCallback(async (text) => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;

    setError(null);

    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: trimmed,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      // Build conversation history for API (excluding current question)
      const historyPayload = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const response = await sendChatMessage(trimmed, historyPayload);

      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        sources: response.sources || [],
        policy_found: response.policy_found ?? true,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setBackendState((prev) => ({ ...prev, status: 'connected' }));
    } catch (err) {
      console.error('Failed to send chat message:', err);
      const isConnectionIssue =
        err.message.includes('Failed to fetch') ||
        err.message.includes('NetworkError') ||
        err.message.includes('timed out');

      if (isConnectionIssue) {
        setBackendState((prev) => ({ ...prev, status: 'disconnected' }));
      }

      setError(err.message || 'An error occurred while contacting the HR Policy Assistant.');
    } finally {
      setIsLoading(false);
    }
  }, [messages, isLoading]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
  }, []);

  return {
    messages,
    isLoading,
    error,
    backendState,
    sendMessage,
    clearChat,
    retryHealth: checkHealth,
  };
}
