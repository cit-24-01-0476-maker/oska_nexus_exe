import { useEffect, useRef, useState } from 'react';
import { ExternalLink, Save, Mail } from 'lucide-react';
import { api, type EmailDraft } from '../services/api';
import { wsClient } from '../services/websocket';

const emptyDraft: EmailDraft = { recipient: '', subject: '', body: '', signature: '' };
export function EmailDraftEditor() {
  const [draft, setDraft] = useState<EmailDraft>(emptyDraft);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const dirty = useRef(false);
  useEffect(() => {
    let disposed = false;
    const apply = (next: EmailDraft | null) => {
      if (disposed) return;
      if (dirty.current) { setMessage('A voice update is available. Save your edits or reload the draft.'); return; }
      setDraft(next || emptyDraft);
    };
    const load = () => api.getEmailDraft().then(result => apply(result.draft)).catch(e => { if (!disposed) setError(e.message); });
    void load();
    const undraft = wsClient.on('email_draft_changed', ({ draft: next }) => apply(next));
    const unconnection = wsClient.on('connection', ({ connected }) => { if (connected) void load(); });
    return () => { disposed = true; undraft(); unconnection(); };
  }, []);
  function update(key: keyof EmailDraft, value: string) {
    dirty.current = true; setMessage(''); setError(''); setDraft(prev => ({ ...prev, [key]: value }));
  }
  async function save(open = false) {
    if (!draft.body.trim() || busy) return;
    setBusy(true); setError('');
    try {
      const result = await api.saveEmailDraft(draft);
      dirty.current = false; setDraft(result.draft);
      if (open) { await api.openEmailDraft(); setMessage('Opened in Gmail. Review the recipient and message there before sending.'); }
      else setMessage('Draft saved. You can ask OSKA to change this draft by voice.');
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  }
  async function reload() {
    try { const result = await api.getEmailDraft(); dirty.current = false; setDraft(result.draft || emptyDraft); setMessage('Draft reloaded.'); setError(''); }
    catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  }
  const field = 'w-full rounded-xl border border-cyan/20 bg-black/40 px-3 py-2.5 text-sm text-white outline-none focus:border-cyan/60';
  return <section className="space-y-4" aria-label="Email draft editor">
    <div className="flex items-center gap-2"><Mail size={18} className="text-cyan" /><h2 className="font-semibold">Email draft</h2><span className="ml-auto text-[10px] tracking-widest text-cyan">LOCAL DRAFT</span></div>
    <p className="text-xs text-muted leading-relaxed">“Draft an email…” → “Sign as…” → review and open in Gmail. Save manual edits before asking for a voice change.</p>
    <label className="block text-xs text-muted">To<input type="email" aria-label="Email recipient" className={`${field} mt-1`} placeholder="Recipient address (optional while drafting)" value={draft.recipient} onChange={e => update('recipient', e.target.value)} /></label>
    <label className="block text-xs text-muted">Subject<input aria-label="Email subject" className={`${field} mt-1`} maxLength={250} value={draft.subject} onChange={e => update('subject', e.target.value)} /></label>
    <label className="block text-xs text-muted">Message<textarea aria-label="Email body" className={`${field} mt-1 resize-y min-h-40`} rows={8} maxLength={20000} value={draft.body} onChange={e => update('body', e.target.value)} /></label>
    <label className="block text-xs text-muted">Signature<input aria-label="Email signature" className={`${field} mt-1`} placeholder="Your name" maxLength={250} value={draft.signature} onChange={e => update('signature', e.target.value)} /></label>
    {error && <p role="alert" className="text-sm text-red-400">{error}</p>}
    {message && <p role="status" className="text-xs text-cyan leading-relaxed">{message}</p>}
    <div className="flex flex-wrap gap-2 text-xs"><button disabled={busy || !draft.body.trim()} onClick={() => save()} className="px-3 py-2 rounded-lg border border-cyan/30 text-cyan flex gap-2 disabled:opacity-40"><Save size={14} />Save draft</button><button disabled={busy || !draft.body.trim()} onClick={() => save(true)} className="px-3 py-2 rounded-lg bg-cyan text-obsidian font-bold flex gap-2 disabled:opacity-40"><ExternalLink size={14} />Open in Gmail</button><button disabled={busy} className="px-3 py-2 text-muted underline" onClick={reload}>Reload</button></div>
  </section>;
}
