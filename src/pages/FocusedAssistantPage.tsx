import { useEffect, useState } from 'react';
import { Mic, Square, LayoutDashboard, Mail, Send, AudioLines } from 'lucide-react';
import { HolographicFace } from '../hologram/HolographicFace';
import { EmailDraftEditor } from '../components/EmailDraftEditor';
import { wsClient } from '../services/websocket';
import type { AssistantState } from '../types/assistant';

interface Props {
  state: AssistantState; waveformLevel: number; lowPowerMode: boolean; transcript: string; response: string;
  connected: boolean; aiProvider: string; onAISettings: () => void; autoConversation: boolean; onListen: () => void; onStop: () => void;
  onToggleConversation: () => void; onCommand: (text: string) => Promise<void>; onDashboard: () => void;
}
const captions: Partial<Record<AssistantState, string>> = {
  LISTENING: 'කතා කරන්න… මම අහගෙන ඉන්නවා.', TRANSCRIBING: 'ඔයා කියපු දේ තේරුම් ගන්නවා…',
  THINKING: 'හිතනවා…', EXECUTING: 'වැඩේ කරමින් ඉන්නවා…', SPEAKING: 'කතා කරනවා…',
  AWAITING_CONFIRMATION: 'ඔයාගේ තහවුරු කිරීම අවශ්‍යයි.', ERROR: 'ආයෙත් උත්සාහ කරමු.',
};
export function FocusedAssistantPage(p: Props) {
  const [input, setInput] = useState('');
  const [showDraft, setShowDraft] = useState(false);
  const [sending, setSending] = useState(false);
  useEffect(() => wsClient.on('email_draft_changed', () => setShowDraft(true)), []);
  async function submit(e: React.FormEvent) {
    e.preventDefault(); if (!input.trim() || sending) return; setSending(true);
    try { await p.onCommand(input.trim()); setInput(''); } finally { setSending(false); }
  }
  const listening = p.state === 'LISTENING' || p.state === 'TRANSCRIBING';
  return <div className="focus-assistant flex-1 min-h-0 flex flex-col bg-black">
    <header className="flex flex-wrap items-center justify-between gap-3 px-7 py-5 border-b border-white/5">
      <div><div className="text-cyan text-sm font-semibold tracking-[0.35em]">OSKA NEXUS</div><div className="mt-1 text-[10px] text-muted tracking-[0.2em]">PERSONAL DESKTOP ASSISTANT</div></div>
      <div className="flex items-center gap-4 text-xs"><span className={p.connected ? 'text-cyan' : 'text-red-400'}>{p.connected ? 'CORE ONLINE' : 'CONNECTING…'}</span><button onClick={p.onAISettings} className="rounded-full border border-cyan/20 px-3 py-1.5 text-cyan">{p.aiProvider === 'local_rules' ? 'Connect AI · Basic commands' : `${p.aiProvider.toUpperCase()} selected`}</button><button onClick={() => setShowDraft(v => !v)} className="text-muted hover:text-cyan flex gap-1.5 items-center"><Mail size={15} />Draft</button><button onClick={p.onDashboard} className="text-muted hover:text-cyan flex gap-1.5 items-center"><LayoutDashboard size={15} />Dashboard</button></div>
    </header>
    <div className="flex-1 min-h-0 flex">
      <div className="flex-1 min-w-0 min-h-0 flex flex-col items-center relative">
        <div className="flex-1 min-h-40 w-full max-w-[650px] relative"><HolographicFace state={p.state} waveformLevel={p.waveformLevel} lowPowerMode={p.lowPowerMode} minimal /></div>
        <div className="w-full max-w-2xl px-6 pb-5 space-y-4 z-10">
          <div className="text-center"><p className="text-[10px] tracking-[0.3em] text-cyan mb-2">{p.state.replaceAll('_', ' ')}</p><p className="text-sm text-white/80">{captions[p.state] || (p.autoConversation ? 'ඔයාගේ ඊළඟ ඉල්ලීම කියන්න.' : 'Microphone එක ඔබලා කතා කරන්න.')}</p></div>
          {p.transcript && <p className="text-xs text-center text-muted max-h-12 overflow-y-auto">“{p.transcript}”</p>}
          {p.response && <p role="status" className="text-sm text-center text-white/90 leading-relaxed max-h-24 overflow-y-auto">{p.response}</p>}
          <div className="flex items-center justify-center gap-3"><button disabled={!p.connected || listening} aria-label="Speak to OSKA" onClick={p.onListen} className={`p-4 rounded-full border border-cyan/50 text-cyan disabled:opacity-40 ${listening ? 'bg-cyan/20 animate-pulse' : 'bg-cyan/10 hover:bg-cyan/20'}`}><Mic size={22} /></button><button disabled={!p.connected} onClick={p.onToggleConversation} className={`px-4 py-2.5 rounded-full border text-xs flex items-center gap-2 ${p.autoConversation ? 'border-cyan text-cyan bg-cyan/10' : 'border-white/15 text-muted'}`}><AudioLines size={15} />{p.autoConversation ? 'Conversation on' : 'Start conversation'}</button><button aria-label="Stop listening" onClick={p.onStop} className="p-3 rounded-full text-muted border border-white/15 hover:text-white"><Square size={15} /></button></div>
          <form onSubmit={submit} className="flex items-center rounded-full border border-white/10 bg-white/[0.025] px-4 py-2"><input aria-label="Ask OSKA" value={input} onChange={e => setInput(e.target.value)} placeholder="කතා කරන්න, නැත්නම් මෙතන ලියන්න…" className="flex-1 min-w-0 bg-transparent text-sm py-1 outline-none placeholder:text-white/25" /><button aria-label="Send command" disabled={!input.trim() || sending || !p.connected} className="text-cyan p-1.5 disabled:opacity-30"><Send size={17} /></button></form>
        </div>
      </div>
      {showDraft && <aside className="w-[380px] max-w-[46vw] border-l border-cyan/15 bg-[#071018] p-5 overflow-y-auto"><div className="flex justify-end mb-3"><button className="text-xs text-muted" onClick={() => setShowDraft(false)}>Close draft panel</button></div><EmailDraftEditor /></aside>}
    </div>
  </div>;
}
