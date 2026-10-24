import { useState, useEffect } from 'react';
import { Bell, Trash2 } from 'lucide-react';
import { api, type Reminder } from '../services/api';
import { wsClient } from '../services/websocket';
export function RemindersPage() {
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [title, setTitle] = useState(''); const [due, setDue] = useState('');
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  async function load() {
    try { setReminders(await api.getReminders()); setError(''); }
    catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }
  useEffect(() => {
  // eslint-disable-next-line react/set-state-in-effect -- Loads backend data asynchronously.
    void load();
    const uncommand = wsClient.on('command_result', () => { void load(); });
    const undue = wsClient.on('reminder_due', () => { void load(); });
    const interval = setInterval(load, 30000);
    return () => { uncommand(); undue(); clearInterval(interval); };
  }, []);
  async function mutate(action: () => Promise<unknown>) {
    setBusy(true);
    try { await action(); await load(); return true; }
    catch (e) { setError(e instanceof Error ? e.message : String(e)); return false; }
    finally { setBusy(false); }
  }
  async function create(e: React.FormEvent) {
    e.preventDefault();
    if (await mutate(() => api.createReminder(title.trim(), due ? new Date(due).getTime() / 1000 : undefined))) { setTitle(''); setDue(''); }
  }
  const field = 'bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-sm text-white';
  return <div className="flex-1 flex flex-col h-full bg-obsidian p-6 overflow-y-auto">
    <h2 className="text-lg font-bold flex gap-2 items-center mb-2"><Bell className="text-cyan w-5" />REMINDERS & SCHEDULE</h2>
    <p className="text-xs text-muted mb-6">Choose a time, or include “in 10 minutes” / “at 5 PM” in the title. Default: one hour. Keep OSKA running to receive alerts.</p>
    {error && <p role="alert" className="text-red-400 text-sm mb-4">{error} <button onClick={load} className="underline">Retry</button></p>}
    <form onSubmit={create} className="flex flex-wrap gap-3 mb-6">
      <input required aria-label="Reminder title" className={`${field} flex-1 min-w-48`} placeholder="Remind me to..." value={title} onChange={e => setTitle(e.target.value)} />
      <input aria-label="Reminder time" type="datetime-local" className={field} value={due} onChange={e => setDue(e.target.value)} />
      <button disabled={busy || !title.trim()} className="bg-cyan text-obsidian px-4 py-2 rounded-xl text-sm font-bold disabled:opacity-40">Add Reminder</button>
    </form>
    <div className="space-y-3">{reminders.map(rem => <div key={rem.id} className="frosted-glass rounded-xl p-4 border border-cyan/20 flex gap-3 items-center">
      <input aria-label={`Complete ${rem.title}`} type="checkbox" disabled={busy} checked={!!rem.completed} onChange={() => mutate(() => api.updateReminder(rem.id, !rem.completed))} className="accent-cyan" />
      <div className="flex-1"><p className={rem.completed ? 'line-through text-muted' : 'text-white'}>{rem.title}</p><time className="text-xs text-muted">{new Date(rem.due_time * 1000).toLocaleString()}</time></div>
      <button disabled={busy} aria-label={`Delete ${rem.title}`} className="text-red-400" onClick={() => mutate(() => api.deleteReminder(rem.id))}><Trash2 size={16} /></button>
    </div>)}</div>
    {!reminders.length && !error && <p className="text-muted text-sm">No reminders yet.</p>}
  </div>;
}
