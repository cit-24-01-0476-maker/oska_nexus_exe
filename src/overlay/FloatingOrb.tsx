import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Sparkles, X } from 'lucide-react';
import { AssistantState } from '../types/assistant';
import { wsClient } from '../services/websocket';
import { api } from '../services/api';

export const FloatingOrb: React.FC = () => {
  const [state, setState] = useState<AssistantState>('IDLE');
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [pending, setPending] = useState<string | null>(null);
  const [waveform, setWaveform] = useState(0);
  const [isExpanded, setIsExpanded] = useState(false);

  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    let disposed = false;
    let unlisten: (() => void) | undefined;
    // Listen for WebSocket events
    const unsubState = wsClient.on('state_change', (data) => {
      setState(data.state);
      setPending(data.context?.pending_confirmation?.pending_action || null);
      if (data.context?.transcript) setTranscript(data.context.transcript);
      if (data.context?.response) setResponse(data.context.response);
      if (data.state === 'LISTENING' || data.state === 'WAKE_DETECTED') {
        setIsExpanded(true);
      }
    });

    const unWake = wsClient.on('wake_detected', () => setIsExpanded(true));
    const unsubWave = wsClient.on('waveform', (data) => {
      setWaveform(data.level || 0);
    });

    const unsubCmd = wsClient.on('command_result', (data) => {
      setPending(data.result?.status === 'REQUIRES_CONFIRMATION' ? data.result.data.pending_action : null);
      if (data.result?.response) {
        setResponse(data.result.response);
      }
      // Auto collapse after 4.5s
      if (closeTimer.current) clearTimeout(closeTimer.current);
      if (data.result?.status !== 'REQUIRES_CONFIRMATION') closeTimer.current = setTimeout(() => { void handleClose(); }, 4500);
    });

    // Check Tauri event if triggered
    if ((window as any).__TAURI_INTERNALS__) {
      import('@tauri-apps/api/event').then(({ listen }) => {
        listen('activated', () => {
          if (closeTimer.current) clearTimeout(closeTimer.current);
          setIsExpanded(true);
          api.startListening().catch((e) => setResponse(e.message));
        }).then((fn) => { if (disposed) fn(); else unlisten = fn; });
      });
    }

    return () => {
      disposed = true;
      unlisten?.();
      if (closeTimer.current) clearTimeout(closeTimer.current);
      unWake();
      unsubState();
      unsubWave();
      unsubCmd();
    };
  }, []);

  async function handleClose() {
    setIsExpanded(false);
    if ((window as any).__TAURI_INTERNALS__) {
      const { invoke } = await import('@tauri-apps/api/core');
      invoke('hide_floating_assistant');
    }
  };

  const handleOrbClick = () => {
    if (!isExpanded) {
      setIsExpanded(true);
      api.startListening().catch((e) => setResponse(e.message));
    } else {
      handleClose();
    }
  };

  return (
    <div className="oska-overlay w-screen h-screen flex flex-col items-center justify-end pb-4 bg-transparent select-none overflow-hidden">
      <AnimatePresence>
        {isExpanded ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.85, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.85, y: 20 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            className="w-[420px] max-h-[236px] rounded-2xl frosted-glass border border-cyan/40 p-4 shadow-cyan-glow relative overflow-y-auto backdrop-blur-xl bg-obsidian-card/90"
          >
            {/* Header / State */}
            <div className="flex items-center justify-between border-b border-cyan/15 pb-2 mb-3">
              <div className="flex items-center space-x-2">
                <div className="w-2.5 h-2.5 rounded-full bg-cyan animate-pulse shadow-cyan-glow" />
                <span className="text-xs font-mono tracking-wider text-cyan font-bold uppercase">
                  OSKA NEXUS • {state}
                </span>
              </div>
              <button
                onClick={handleClose}
                className="text-muted hover:text-white transition-colors p-1 rounded-lg hover:bg-white/5"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Dynamic Waveform bar */}
            <div className="h-1.5 w-full bg-navy-light rounded-full overflow-hidden mb-3 relative">
              <motion.div
                className="h-full bg-gradient-to-r from-cyan via-ice to-violet rounded-full"
                animate={{ width: `${Math.max(8, waveform * 100)}%` }}
                transition={{ duration: 0.05 }}
              />
            </div>

            {/* Speech Transcript */}
            <div className="min-h-[48px] flex flex-col justify-center mb-2">
              {transcript ? (
                <div className="text-sm text-ice font-medium italic">
                  "{transcript}"
                </div>
              ) : (
                <div className="text-xs text-muted flex items-center space-x-2">
                  <Mic className="w-3.5 h-3.5 text-cyan animate-bounce" />
                  <span>Listening for command...</span>
                </div>
              )}
            </div>

            {pending && <div className="flex gap-4 mb-2 text-xs">{[true, false].map(confirmed => <button key={String(confirmed)} className="px-3 py-2 border border-cyan rounded-lg" onClick={() => api.confirmPowerAction(pending, confirmed).then(() => setPending(null)).catch(e => setResponse(e.message))}>{confirmed ? 'Confirm power action' : 'Cancel'}</button>)}</div>}
            {/* Response Area */}
            {response && (
              <motion.div
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-xs text-white/90 bg-navy/60 rounded-xl p-2.5 border border-cyan/20 flex items-start space-x-2"
              >
                <Sparkles className="w-3.5 h-3.5 text-cyan shrink-0 mt-0.5" />
                <div className="leading-relaxed">{response}</div>
              </motion.div>
            )}
          </motion.div>
        ) : (
          <motion.button
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            onClick={handleOrbClick}
            className="w-14 h-14 rounded-full bg-obsidian-card/90 border border-cyan/50 shadow-cyan-glow flex items-center justify-center cursor-pointer hover:border-cyan hover:scale-105 transition-all group backdrop-blur-md"
          >
            <div className="w-10 h-10 rounded-full border border-violet/50 flex items-center justify-center animate-pulse-slow">
              <div className="w-5 h-5 rounded-full bg-cyan/30 flex items-center justify-center">
                <Mic className="w-4 h-4 text-cyan group-hover:text-white transition-colors" />
              </div>
            </div>
          </motion.button>
        )}
      </AnimatePresence>
    </div>
  );
};
