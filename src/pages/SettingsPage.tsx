import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Mic, 
  Volume2, 
  Cpu, 
  Monitor, 
  Check, 
  AlertCircle, 
  Save, 
  Play, 
  Radio 
} from 'lucide-react';
import { AudioDevice, TTSVoice } from '../types/assistant';
import { api } from '../services/api';

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<Record<string, string>>({});
  const [devices, setDevices] = useState<AudioDevice[]>([]);
  const [voices, setVoices] = useState<TTSVoice[]>([]);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [wakeStatus, setWakeStatus] = useState('UNINITIALIZED');
  const [wakeError, setWakeError] = useState('');



  async function loadAll() {
    try {
      const [st, devs, vcs, currState] = await Promise.all([
        api.getSettings(),
        api.getAudioDevices(),
        api.getTTSVoices(),
        api.getState(),
      ]);
      setSettings(st);
      setDevices(devs);
      setVoices(vcs);
      setWakeStatus(currState.wake_status);
      setWakeError(currState.wake_error);
    } catch (e) { setWakeError(e instanceof Error ? e.message : String(e)); }
  };

  useEffect(() => {
  // eslint-disable-next-line react/set-state-in-effect -- Loads backend data asynchronously.
    loadAll();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.updateSettings(settings);
      setSettings(res.settings);
      setSavedSuccess(true);
      const currState = await api.getState();
      setWakeStatus(currState.wake_status);
      setWakeError(currState.wake_error);
      setTimeout(() => setSavedSuccess(false), 2500);
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const updateKey = (k: string, v: string) => {
    setSettings((prev) => ({ ...prev, [k]: v }));
  };

  const handleTestVoice = async () => {
    try { await api.testVoice(); } catch (e) { alert(e instanceof Error ? e.message : String(e)); }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-obsidian p-6 overflow-y-auto">
      <div className="flex items-center justify-between pb-4 border-b border-cyan/15 mb-6">
        <div>
          <h2 className="text-lg font-bold text-white tracking-wide flex items-center space-x-2">
            <Settings className="w-5 h-5 text-cyan" />
            <span>ASSISTANT CONFIGURATION</span>
          </h2>
          <p className="text-xs text-muted">
            Configure microphone, wake-word detection, speech synthesis, AI providers, and Windows integration.
          </p>
        </div>
        <button
          onClick={handleSave}
          className="px-5 py-2 rounded-xl bg-cyan hover:bg-cyan/80 text-obsidian text-xs font-bold transition-all shadow-cyan-glow flex items-center space-x-2"
        >
          {savedSuccess ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
          <span>{savedSuccess ? 'Saved' : 'Save Changes'}</span>
        </button>
      </div>

      <form onSubmit={handleSave} className="space-y-6 max-w-4xl">
        <div className="frosted-glass rounded-2xl p-5 border border-cyan/20 bg-navy/40 space-y-3">
          <label className="text-xs text-muted block">Your name (optional email signature)<input aria-label="Your name" value={settings.display_name || ''} onChange={e => updateKey('display_name', e.target.value)} className="mt-1 w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-sm text-white" /></label>
          <label className="text-xs text-muted block">Speech language<select aria-label="Speech language" value={settings.speech_language || 'auto'} onChange={e => updateKey('speech_language', e.target.value)} className="mt-1 w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-sm text-white"><option value="auto">Sinhala / English (Auto)</option><option value="si">Sinhala</option><option value="en">English</option></select></label>
          <label className="text-xs text-muted block">Offline speech model<select aria-label="Offline speech model" value={settings.stt_model || 'base'} onChange={e => updateKey('stt_model', e.target.value)} className="mt-1 w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-sm text-white">{['tiny','base','small','medium','large-v3'].map(model => <option key={model} value={model}>{model}</option>)}</select></label>
          <p className="text-xs text-muted">Larger models take more RAM and processing time. The selected model downloads on first offline use. Sinhala neural speech uses the selected Sinhala voice and requires internet.</p>
        </div>
        {/* Section 1: Audio Input (Microphone) */}
        <div className="frosted-glass rounded-2xl p-5 border border-cyan/20 bg-navy/40 space-y-4">
          <div className="flex items-center space-x-2 text-sm font-bold text-white">
            <Mic className="w-4 h-4 text-cyan" />
            <span>AUDIO INPUT & MICROPHONE</span>
          </div>
          <div>
            <label className="text-xs text-muted block mb-1">Target Microphone Device</label>
            <select
              className="w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-xs text-white"
              onChange={(e) => updateKey('selected_mic_device', e.target.value)}
              value={settings.selected_mic_device || ''}
            >
              <option value="">Default System Microphone</option>
              {devices.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} {d.default ? '(Default)' : ''}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Section 2: Wake Word Engine ("Hey Oska") */}
        <div className="frosted-glass rounded-2xl p-5 border border-cyan/20 bg-navy/40 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-sm font-bold text-white">
              <Radio className="w-4 h-4 text-cyan" />
              <span>WAKE-WORD ENGINE (PICOVOICE PORCUPINE)</span>
            </div>
            <span
              className={`text-[10px] font-mono px-2.5 py-0.5 rounded-full border ${
                wakeStatus === 'READY' || wakeStatus === 'LISTENING'
                  ? 'bg-green-500/20 text-green-400 border-green-500/40'
                  : 'bg-amber-500/20 text-amber-400 border-amber-500/40'
              }`}
            >
              STATUS: {wakeStatus}
            </span>
          </div>

          {wakeError && (
            <div className="text-xs text-amber-400 bg-amber-500/10 border border-amber-500/30 rounded-xl p-3 flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <div>{wakeError}</div>
            </div>
          )}

          <div>
            <label className="text-xs text-muted block mb-1">
              Picovoice AccessKey (Free from console.picovoice.ai)
            </label>
            <input
              type="password"
              value={settings.porcupine_access_key || ''}
              onChange={(e) => updateKey('porcupine_access_key', e.target.value)}
              placeholder="Paste your Picovoice AccessKey here..."
              className="w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-xs text-white font-mono"
            />
          </div>

          <div>
            <label className="text-xs text-muted block mb-1">
              Custom .ppn Model Path (Leave empty to use built-in keywords)
            </label>
            <input
              type="text"
              value={settings.porcupine_keyword_path || ''}
              onChange={(e) => updateKey('porcupine_keyword_path', e.target.value)}
              placeholder="C:\path\to\Hey-Oska_windows.ppn"
              className="w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-xs text-white font-mono"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-muted">Detection Sensitivity</span>
              <span className="font-mono text-cyan">{settings.porcupine_sensitivity || '0.5'}</span>
            </div>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              value={settings.porcupine_sensitivity || '0.5'}
              onChange={(e) => updateKey('porcupine_sensitivity', e.target.value)}
              className="w-full accent-cyan"
            />
          </div>
        </div>

        {/* Section 3: Speech Synthesis (TTS) */}
        <div className="frosted-glass rounded-2xl p-5 border border-cyan/20 bg-navy/40 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-sm font-bold text-white">
              <Volume2 className="w-4 h-4 text-cyan" />
              <span>TEXT-TO-SPEECH (TTS) ENGINE</span>
            </div>
            <button
              type="button"
              onClick={handleTestVoice}
              className="px-3 py-1 rounded-lg bg-cyan/15 hover:bg-cyan/30 text-cyan text-xs font-semibold flex items-center space-x-1"
            >
              <Play className="w-3 h-3 fill-current" />
              <span>Test Voice</span>
            </button>
          </div>

          <div>
            <label className="text-xs text-muted block mb-1">Installed Windows Voices</label>
            <select
              className="w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-xs text-white"
              onChange={(e) => updateKey('tts_voice_id', e.target.value)}
              value={settings.tts_voice_id || ''}
            >
              <option value="">Automatic Sinhala / English voice (Windows fallback)</option>
              {voices.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-muted block mb-1">Speaking Rate (Words/Min)</label>
              <input
                type="number"
                min="100"
                max="300"
                value={settings.tts_rate || '180'}
                onChange={(e) => updateKey('tts_rate', e.target.value)}
                className="w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-xs text-white"
              />
            </div>
            <div>
              <label className="text-xs text-muted block mb-1">Speech Volume (0.0 to 1.0)</label>
              <input
                type="number"
                min="0.1"
                max="1.0"
                step="0.1"
                value={settings.tts_volume || '1.0'}
                onChange={(e) => updateKey('tts_volume', e.target.value)}
                className="w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-xs text-white"
              />
            </div>
          </div>
        </div>

        {/* Section 4: AI Brain & LLM Provider */}
        <div className="frosted-glass rounded-2xl p-5 border border-cyan/20 bg-navy/40 space-y-4">
          <div className="flex items-center space-x-2 text-sm font-bold text-white">
            <Cpu className="w-4 h-4 text-cyan" />
            <span>AI BRAIN & REASONING PROVIDER</span>
          </div>

          <div>
            <label className="text-xs text-muted block mb-1">Intelligence Layer</label>
            <select
              value={settings.llm_provider || 'local_rules'}
              onChange={(e) => {
                const provider = e.target.value;
                updateKey('llm_provider', provider);
                if (provider === 'xai') { updateKey('xai_model', settings.xai_model || 'grok-4.7'); return; }
                const defaults: Record<string,string> = { gemini: 'gemini-3.1-flash-lite', openai: 'gpt-4o-mini', ollama: 'llama3' };
                const current = settings.llm_model || '';
                const keepCurrent = provider === 'gemini' ? current.startsWith('gemini-') : provider === 'openai' ? current.startsWith('gpt-') : provider === 'ollama' && current && !current.startsWith('gemini-') && !current.startsWith('gpt-');
                updateKey('llm_model', keepCurrent ? current : defaults[provider] || '');
              }}
              className="w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-xs text-white"
            >
              <option value="local_rules">Layer 1: Local Rule Engine (100% Offline, Fast)</option>
              <option value="ollama">Layer 2: Local Ollama (Self-Hosted LLM)</option>
              <option value="openai">Layer 2: OpenAI API</option>
              <option value="gemini">Layer 2: Google Gemini API</option>
              <option value="xai">Layer 2: xAI / Grok API (separate API billing)</option>
            </select>
          </div>

          {settings.llm_provider === 'ollama' && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-muted block mb-1">Ollama Endpoint</label>
                <input
                  type="text"
                  value={settings.ollama_endpoint || 'http://localhost:11434'}
                  onChange={(e) => updateKey('ollama_endpoint', e.target.value)}
                  className="w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-xs text-white font-mono"
                />
              </div>
              <div>
                <label className="text-xs text-muted block mb-1">Model Name</label>
                <input
                  type="text"
                  value={settings.llm_model || 'llama3'}
                  onChange={(e) => updateKey('llm_model', e.target.value)}
                  className="w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-xs text-white font-mono"
                />
              </div>
            </div>
          )}

          {(['openai', 'gemini', 'xai'].includes(settings.llm_provider)) && <div>
            <label className="text-xs text-muted block mb-1">Model Name</label>
            <input aria-label="AI model name" className="w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-xs text-white" value={(settings.llm_provider === 'xai' ? settings.xai_model : settings.llm_model) || ''} onChange={e => updateKey(settings.llm_provider === 'xai' ? 'xai_model' : 'llm_model', e.target.value)} />
          </div>}
          {(['openai', 'gemini', 'xai'].includes(settings.llm_provider)) && (
            <div>
              <label className="text-xs text-muted block mb-1">
                {settings.llm_provider.toUpperCase()} API Key
              </label>
              <input
                type="password"
                value={(settings.llm_provider === 'xai' ? settings.xai_api_key : settings.llm_api_key) || ''}
                onChange={(e) => updateKey(settings.llm_provider === 'xai' ? 'xai_api_key' : 'llm_api_key', e.target.value)}
                placeholder={settings.llm_provider === 'xai' ? 'xai-...' : 'API key'}
                className="w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-xs text-white font-mono"
              />
            </div>
          )}
        </div>

        {settings.llm_provider === 'xai' && <p className="text-xs text-muted">Grok (xAI) and Groq are different providers. xAI needs its own API credits or license. Its key and model are saved separately from Gemini/OpenAI.</p>}

        {/* Section 5: Windows Desktop & System Tray Integration */}
        <div className="frosted-glass rounded-2xl p-5 border border-cyan/20 bg-navy/40 space-y-4">
          <div className="flex items-center space-x-2 text-sm font-bold text-white">
            <Monitor className="w-4 h-4 text-cyan" />
            <span>WINDOWS SYSTEM TRAY & STARTUP</span>
          </div>

          <div className="flex items-center justify-between py-2 border-b border-cyan/10">
            <div>
              <div className="text-xs text-white font-medium">Minimize to System Tray</div>
              <div className="text-[11px] text-muted">
                Closing the main window minimizes OSKA to the Windows tray to keep wake listening active.
              </div>
            </div>
            <input
              type="checkbox"
              checked={settings.minimize_to_tray !== 'false'}
              onChange={(e) => updateKey('minimize_to_tray', e.target.checked ? 'true' : 'false')}
              className="accent-cyan w-4 h-4"
            />
          </div>

          <div className="flex items-center justify-between py-2">
            <div>
              <div className="text-xs text-white font-medium">Launch at Windows Login</div>
              <div className="text-[11px] text-muted">
                Start OSKA NEXUS minimized in the background when logging into Windows.
              </div>
            </div>
            <input
              type="checkbox"
              checked={settings.start_with_windows === 'true'}
              onChange={(e) => updateKey('start_with_windows', e.target.checked ? 'true' : 'false')}
              className="accent-cyan w-4 h-4"
            />
          </div>
        </div>
      </form>
    </div>
  );
};
