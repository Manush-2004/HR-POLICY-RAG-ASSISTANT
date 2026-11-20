/**
 * API client service for communicating with FastAPI backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Check backend health and readiness.
 * @returns {Promise<{status: string, policy_pdf_present: boolean, vector_store_initialized: boolean, llm_configured: boolean}>}
 */
export async function fetchHealth() {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 6000);

  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`Health check failed with status: ${response.status}`);
    }
    return await response.json();
  } catch (err) {
    clearTimeout(timeoutId);
    throw new Error(err.message || 'Health check network error', { cause: err });
  }
}

/**
 * Send an employee query to the RAG chat endpoint.
 * @param {string} message - User query.
 * @param {Array<{role: string, content: string}>} history - Conversation history.
 * @returns {Promise<{answer: string, sources: Array<{source: string, page: number, snippet: string}>, policy_found: boolean}>}
 */
export async function sendChatMessage(message, history = []) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout for RAG reasoning

  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        message: message.trim(),
        history: history.map((item) => ({
          role: item.role,
          content: item.content,
        })),
      }),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorDetail = `Request failed (${response.status})`;
      try {
        const errorData = await response.json();
        errorDetail = errorData.detail || errorDetail;
      } catch {
        // fallback
      }
      throw new Error(errorDetail);
    }

    return await response.json();
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error('Request timed out. The server took too long to generate a response.', { cause: err });
    }
    throw new Error(err.message || 'Error communicating with backend', { cause: err });
  }
}
