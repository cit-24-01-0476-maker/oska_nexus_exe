import type { AssistantState, AssistantContext, SystemMetrics, Routine, ChatMessage, AudioDevice, TTSVoice } from '../types/assistant';
export const BACKEND_URL = import.meta.env.VITE_OSKA_API_URL || 'http://127.0.0.1:8765';
export interface Note { id: number; title: string; content: string; updated_at: number }
export interface Reminder { id: number; title: string; due_time: number; completed: number }
export interface EmailDraft { id?: number; recipient: string; subject: string; body: string; signature: string; updated_at?: number }
export async function request<T = any>(path: string, options: RequestInit = {}): Promise<T> {
  let res: Response;
  try { res = await fetch(`${BACKEND_URL}${path}`, { ...options, signal: AbortSignal.timeout(90000), headers: { 'Content-Type': 'application/json', ...options.headers } }); }
  catch { throw new Error('Cannot reach the OSKA backend. Check that the desktop core is running.'); }
  const data = await res.json();
  if (!res.ok || data.status === 'FAILED') throw new Error(typeof data.detail === 'string' ? data.detail : data.response || data.message || `Request failed (${res.status}).`);
  return data;
}
const body = (method: string, data?: unknown): RequestInit => ({ method, ...(data === undefined ? {} : { body: JSON.stringify(data) }) });
export const api = {
  getState: () => request<{ state: AssistantState; context: AssistantContext; wake_status: string; wake_error: string }>('/api/state'),
  getSettings: () => request<Record<string, string>>('/api/settings'),
  async updateSettings(settings: Record<string, string>) {
    if ((window as any).__TAURI_INTERNALS__) {
      const { invoke } = await import('@tauri-apps/api/core');
      await invoke('apply_desktop_settings', { settings });
    }
    return request<{ status: string; settings: Record<string, string> }>('/api/settings', body('POST', { settings }));
  },
  sendCommand: (text: string) => request('/api/command', body('POST', { text })),
  startListening: () => request('/api/voice/listen', body('POST')),
  stopListening: () => request('/api/voice/stop', body('POST')),
  getEmailDraft: () => request<{draft: EmailDraft | null}>('/api/email/draft'),
  saveEmailDraft: (draft: EmailDraft) => request<{draft: EmailDraft}>('/api/email/draft', body('PUT', draft)),
  openEmailDraft: () => request('/api/email/open', body('POST')),
  toggleWakeWord: () => request<{ enabled: boolean; listening: boolean; status: string; error?: string }>('/api/wake/toggle', body('POST')),
  toggleAutoConversation: () => request<{ auto_conversation: boolean }>('/api/auto_conversation/toggle', body('POST')),
  getAudioDevices: () => request<AudioDevice[]>('/api/audio/devices'),
  getTTSVoices: () => request<TTSVoice[]>('/api/tts/voices'),
  testVoice: () => request('/api/tts/test', body('POST')),
  getChatHistory: () => request<ChatMessage[]>('/api/chat/history'),
  clearChatHistory: () => request('/api/chat/history', body('DELETE')),
  getMetrics: () => request<SystemMetrics>('/api/metrics'),
  getRoutines: () => request<Routine[]>('/api/routines'),
  createRoutine: (data: unknown) => request('/api/routines', body('POST', data)),
  runRoutine: (id: string) => request(`/api/routines/${encodeURIComponent(id)}/run`, body('POST')),
  getReminders: () => request<Reminder[]>('/api/reminders'),
  createReminder: (title: string, due_time?: number) => request('/api/reminders', body('POST', { title, due_time })),
  updateReminder: (id: number, completed: boolean) => request(`/api/reminders/${id}`, body('PATCH', { completed })),
  deleteReminder: (id: number) => request(`/api/reminders/${id}`, body('DELETE')),
  getNotes: () => request<Note[]>('/api/notes'),
  saveNote: (note: { id?: number; title: string; content: string }) => request(`/api/notes${note.id ? `/${note.id}` : ''}`, body(note.id ? 'PUT' : 'POST', note)),
  deleteNote: (id: number) => request(`/api/notes/${id}`, body('DELETE')),
  getAudit: () => request<any[]>('/api/audit'),
  confirmPowerAction: (action: string, confirmed: boolean) => request('/api/power/confirm', body('POST', { action, confirmed })),
};
