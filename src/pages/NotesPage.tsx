import { useState, useEffect } from 'react';
import { FileText, Plus, Search, Pencil, Trash2 } from 'lucide-react';
import { api, type Note } from '../services/api';
import { wsClient } from '../services/websocket';
export function NotesPage() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [search, setSearch] = useState('');
  const [draft, setDraft] = useState<{ id?: number; title: string; content: string } | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function loadNotes() {
    try { setNotes(await api.getNotes()); setError(''); }
    catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }
  // eslint-disable-next-line react/set-state-in-effect -- Loads backend data asynchronously.
  useEffect(() => { void loadNotes(); return wsClient.on('command_result', () => { void loadNotes(); }); }, []);
  async function save(e: React.FormEvent) {
    e.preventDefault(); if (!draft || busy) return; setBusy(true);
    try { await api.saveNote(draft); setDraft(null); await loadNotes(); }
    catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  }
  async function remove(id: number) {
    try { await api.deleteNote(id); await loadNotes(); }
    catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }
  const field = 'w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-sm text-white';
  return <div className="flex-1 flex flex-col h-full bg-obsidian p-6 overflow-y-auto">
    <div className="flex justify-between items-center border-b border-cyan/15 pb-4 mb-6">
      <h2 className="text-lg font-bold flex gap-2 items-center"><FileText className="text-cyan w-5" />NOTES & KNOWLEDGE</h2>
      <button onClick={() => setDraft({ title: '', content: '' })} className="bg-cyan text-obsidian px-4 py-2 rounded-xl text-xs font-bold flex gap-2"><Plus size={16} />New Note</button>
    </div>
    {error && <p role="alert" className="text-red-400 text-sm mb-4">{error} <button onClick={loadNotes} className="underline">Retry</button></p>}
    {draft && <form onSubmit={save} className="space-y-3 frosted-glass p-4 rounded-xl mb-5">
      <input aria-label="Note title" required maxLength={200} className={field} placeholder="Title" value={draft.title} onChange={e => setDraft({ ...draft, title: e.target.value })} />
      <textarea aria-label="Note content" required rows={6} className={field} placeholder="Write your note..." value={draft.content} onChange={e => setDraft({ ...draft, content: e.target.value })} />
      <div className="flex gap-3"><button disabled={busy || !draft.title.trim() || !draft.content.trim()} className="bg-cyan text-obsidian px-4 py-2 rounded-lg disabled:opacity-40">{busy ? 'Saving...' : 'Save Note'}</button><button type="button" onClick={() => setDraft(null)}>Cancel</button></div>
    </form>}
    <div className="relative mb-5"><Search className="absolute left-3 top-2.5 w-4 text-muted" /><input aria-label="Search notes" className={`${field} pl-9`} placeholder="Search notes..." value={search} onChange={e => setSearch(e.target.value)} /></div>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {notes.filter(n => `${n.title} ${n.content}`.toLowerCase().includes(search.toLowerCase())).map(note => <article key={note.id} className="frosted-glass rounded-xl border border-cyan/20 p-4">
        <h3 className="font-bold mb-2 break-words">{note.title}</h3><p className="text-sm text-white/80 whitespace-pre-wrap break-words">{note.content}</p>
        <div className="flex items-center gap-3 mt-4 text-xs text-muted"><time>{new Date(note.updated_at * 1000).toLocaleDateString()}</time><button aria-label={`Edit ${note.title}`} onClick={() => setDraft(note)} className="ml-auto text-cyan"><Pencil size={16} /></button><button aria-label={`Delete ${note.title}`} onClick={() => remove(note.id)} className="text-red-400"><Trash2 size={16} /></button></div>
      </article>)}
      {!notes.length && !error && <p className="text-muted text-sm">No notes yet. Create one or say “note down…”</p>}
    </div>
  </div>;
}
