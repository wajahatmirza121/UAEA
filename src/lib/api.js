/**
 * UAEA API Client — talks to the uaea-backend FastAPI service.
 *
 * All API calls go through this module. The base URL is read from
 * VITE_API_URL (Vite env variable) or defaults to localhost:8000.
 *
 * Usage:
 *   import { api } from './api';
 *   const reply = await api.chatMessage('session-123', 'What is the fee for BS CS?');
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ── Helpers ────────────────────────────────────────────────────────────────

async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const resp = await fetch(url, { ...options, headers });

  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.detail || `API error ${resp.status}`);
  }

  return resp.json();
}

// ── Chat ───────────────────────────────────────────────────────────────────

/**
 * Send a chat message and get the assistant's reply.
 * @param {string} sessionId  Session/conversation identifier
 * @param {string} text       User message text
 * @param {string} channel    Channel (default: 'web')
 * @returns {Promise<{reply, intent, tool_calls, escalated, confidence, language, sources}>}
 */
export async function chatMessage(sessionId, text, channel = 'web') {
  return request('/v1/chat/message', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, channel, text }),
  });
}

/**
 * Get full conversation history for a session.
 * @param {string} sessionId
 * @returns {Promise<{id, session_id, channel, started_at, resolved, escalated, messages}>}
 */
export async function getSession(sessionId) {
  return request(`/v1/chat/session/${encodeURIComponent(sessionId)}`);
}

/**
 * Create an escalation ticket.
 * @param {string} sessionId
 * @param {string} reason
 * @returns {Promise<{ticket_id, status}>}
 */
export async function escalate(sessionId, reason) {
  return request('/v1/chat/escalate', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, reason }),
  });
}

// ── Lookup ─────────────────────────────────────────────────────────────────

/**
 * List departments, optionally filtered.
 * @param {Object} params  { region?, query? }
 */
export async function getDepartments(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return request(`/v1/lookup/departments${qs ? '?' + qs : ''}`);
}

/**
 * List fee tariffs.
 * @param {Object} params  { program?, category? }
 */
export async function getFeeTariffs(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return request(`/v1/lookup/fee-tariff${qs ? '?' + qs : ''}`);
}

/**
 * List deadlines.
 * @param {Object} params  { service? }
 */
export async function getDeadlines(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return request(`/v1/lookup/deadlines${qs ? '?' + qs : ''}`);
}

/**
 * Get document checklist for a service.
 * @param {string} service
 */
export async function getDocumentChecklist(service) {
  return request(`/v1/lookup/document-checklist?service=${encodeURIComponent(service)}`);
}

// ── Admin (requires API key) ───────────────────────────────────────────────

const adminHeaders = (apiKey) => ({ 'X-API-Key': apiKey });

/**
 * Create a FAQ knowledge chunk (admin).
 */
export async function createFAQ(data, apiKey) {
  return request('/v1/admin/content/faq', {
    method: 'POST',
    headers: adminHeaders(apiKey),
    body: JSON.stringify(data),
  });
}

/**
 * Create a fee tariff entry (admin).
 */
export async function createFeeTariff(data, apiKey) {
  return request('/v1/admin/content/fee-tariff', {
    method: 'POST',
    headers: adminHeaders(apiKey),
    body: JSON.stringify(data),
  });
}

/**
 * Get intent analytics (admin).
 */
export async function getIntentAnalytics(apiKey) {
  return request('/v1/admin/analytics/intents', {
    headers: adminHeaders(apiKey),
  });
}

/**
 * Get unanswered queries queue (admin).
 */
export async function getUnansweredQueue(apiKey) {
  return request('/v1/admin/queue/unanswered', {
    headers: adminHeaders(apiKey),
  });
}

// ── Export as default api object ───────────────────────────────────────────

export const api = {
  chatMessage,
  getSession,
  escalate,
  getDepartments,
  getFeeTariffs,
  getDeadlines,
  getDocumentChecklist,
  createFAQ,
  createFeeTariff,
  getIntentAnalytics,
  getUnansweredQueue,
};

export default api;
