import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Send, Sparkles, AlertTriangle } from 'lucide-react';
import { HolographicFace } from '../hologram/HolographicFace';
import { AssistantState } from '../types/assistant';

interface HomePageProps {
  state: AssistantState;
  waveformLevel: number;
  lowPowerMode: boolean;
  transcript: string;
  response: string;
  onExecuteCommand: (text: string) => void;
  onStartListening: () => void;
  pendingConfirmation: any | null;
  onConfirmAction: (action: string, confirmed: boolean) => void;
}

export const HomePage: React.FC<HomePageProps> = ({
  state,
  waveformLevel,
  lowPowerMode,
  transcript,
  response,
  onExecuteCommand,
  onStartListening,
  pendingConfirmation,
  onConfirmAction,
}) => {
  const [inputText, setInputText] = useState('');
  const [timeStr, setTimeStr] = useState('');
  const [dateStr, setDateStr] = useState('');

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
      setDateStr(now.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' }));
    };
    updateClock();
    const timer = setInterval(updateClock, 1000);
    return () => clearInterval(timer);
  }, []);

  const quickCommands = [
    'Screenshot එකක් ගන්න',
    'Desktop එක පෙන්වන්න',
    'Open YouTube',
    'Type Hello OSKA',
    'Window එක minimize කරන්න',
    'Empty Recycle Bin',
    'Task Manager',
    'What time is it?',
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputText.trim()) {
      onExecuteCommand(inputText.trim());
      setInputText('');
    }
  };

  const isListening = state === 'LISTENING' || state === 'WAKE_DETECTED';

  return (
    <div className="flex-1 flex flex-col h-full relative overflow-hidden bg-obsidian">
      {/* Cinematic Top-Left HUD (Matching video reference) */}
      <div className="absolute top-6 left-8 z-20 pointer-events-none select-none">
        <div className="flex items-center space-x-2 text-[11px] font-mono tracking-[0.35em] text-cyan font-bold uppercase drop-shadow-md">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan inline-block shadow-cyan-glow animate-pulse" />
          <span>O . S . K . A . &nbsp; N . E . X . U . S .</span>
        </div>
        <div className="text-[11px] font-mono text-muted/80 tracking-wider mt-1">
          <span className="text-white/90 font-semibold">{timeStr}</span> &nbsp;&nbsp; {dateStr}
        </div>
      </div>

      {/* Center 3D Interactive Holographic Face (Matching reference video) */}
      <div className="flex-1 relative flex items-center justify-center min-h-[420px]">
        <div className="absolute inset-0">
          <HolographicFace
            state={state}
            waveformLevel={waveformLevel}
            lowPowerMode={lowPowerMode}
          />
        </div>

        {/* Confirmation Modal */}
        <AnimatePresence>
          {pendingConfirmation && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="absolute z-30 p-6 rounded-2xl frosted-glass border border-red-500/50 shadow-2xl bg-obsidian-darker/95 max-w-md w-full mx-4"
            >
              <div className="flex items-center space-x-3 text-red-400 mb-3">
                <AlertTriangle className="w-5 h-5" />
                <h3 className="font-bold tracking-wide">CONFIRMATION REQUIRED</h3>
              </div>
              <p className="text-sm text-white/90 mb-5 leading-relaxed">
                {pendingConfirmation.pending_action === 'request_shutdown'
                  ? 'OSKA is requesting permission to shut down your computer. Do you want to proceed?'
                  : 'OSKA is requesting permission to restart your computer. Do you want to proceed?'}
              </p>
              <div className="flex space-x-3 justify-end">
                <button
                  type="button"
                  onClick={() => onConfirmAction(pendingConfirmation.pending_action, false)}
                  className="px-4 py-2 rounded-xl border border-white/10 text-xs font-semibold hover:bg-white/5 transition-all"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => onConfirmAction(pendingConfirmation.pending_action, true)}
                  className="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-semibold shadow-lg transition-all"
                >
                  Confirm & Execute
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Transcript & Response Display Overlay */}
      <div className="px-8 pb-5 z-10 flex flex-col items-center">
        {/* Dynamic response card */}
        {(transcript || response) && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-2xl bg-navy/80 rounded-2xl p-4 border border-cyan/25 shadow-cyan-glow mb-3 backdrop-blur-md"
          >
            {transcript && (
              <div className="text-xs text-muted font-mono mb-1 flex items-center space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan inline-block" />
                <span>USER:</span>
                <span className="text-ice font-sans italic font-normal">"{transcript}"</span>
              </div>
            )}
            {response && (
              <div className="text-sm text-white font-medium flex items-start space-x-2.5 mt-1">
                <Sparkles className="w-4 h-4 text-cyan shrink-0 mt-0.5" />
                <div className="leading-relaxed">{response}</div>
              </div>
            )}
          </motion.div>
        )}

        {/* Quick action chips */}
        <div className="w-full max-w-2xl flex flex-wrap gap-2 justify-center mb-3">
          {quickCommands.map((cmd) => (
            <button
              key={cmd}
              type="button"
              onClick={() => onExecuteCommand(cmd)}
              className="text-xs px-3 py-1.5 rounded-full bg-navy/50 hover:bg-cyan/15 text-muted hover:text-cyan border border-cyan/15 hover:border-cyan/40 transition-all font-medium"
            >
              {cmd}
            </button>
          ))}
        </div>

        {/* Command Input Bar & Microphone button */}
        <div className="w-full max-w-2xl">
          <form
            onSubmit={handleSubmit}
            className="frosted-glass rounded-2xl p-2 border border-cyan/25 flex items-center space-x-2 shadow-2xl bg-obsidian-card/90"
          >
            {/* Push-to-talk mic button */}
            <button
              type="button"
              onClick={onStartListening}
              className={`w-11 h-11 rounded-xl flex items-center justify-center transition-all ${
                isListening
                  ? 'bg-cyan text-obsidian shadow-cyan-glow scale-105 animate-pulse'
                  : 'bg-cyan/10 text-cyan hover:bg-cyan hover:text-obsidian'
              }`}
              title="Click to speak (Push to talk)"
            >
              <Mic className="w-5 h-5" />
            </button>

            {/* Input field */}
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Ask anything or command OSKA (e.g. 'Coding mode', 'Open VS Code', 'What time is it?')"
              className="flex-1 bg-transparent px-3 py-2 text-sm text-white placeholder-muted focus:outline-none"
            />

            {/* Submit button */}
            <button
              type="submit"
              disabled={!inputText.trim()}
              className="w-10 h-10 rounded-xl bg-cyan/10 hover:bg-cyan text-cyan hover:text-obsidian flex items-center justify-center transition-all disabled:opacity-30 disabled:hover:bg-cyan/10 disabled:hover:text-cyan"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
