import React from 'react';
import { Radio, Zap, MessageSquareCode } from 'lucide-react';
import { AssistantState } from '../types/assistant';

interface HeaderProps {
  state: AssistantState;
  wakeWordEnabled: boolean;
  wakeWordStatus: string;
  onToggleWakeWord: () => void;
  autoConversation: boolean;
  onToggleAutoConversation: () => void;
  lowPowerMode: boolean;
  onToggleLowPower: () => void;
  onOpenSettings: () => void;
  onEnterFocus: () => void;
  isBackendConnected: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  state,
  wakeWordEnabled,
  wakeWordStatus,
  onToggleWakeWord,
  autoConversation,
  onToggleAutoConversation,
  lowPowerMode,
  onToggleLowPower,
  onOpenSettings,
  onEnterFocus,
  isBackendConnected,
}) => {
  const getStateColor = (st: AssistantState) => {
    switch (st) {
      case 'LISTENING':
      case 'WAKE_DETECTED':
        return 'bg-cyan text-obsidian border-cyan shadow-cyan-glow';
      case 'THINKING':
        return 'bg-violet text-white border-violet shadow-violet-glow';
      case 'SPEAKING':
        return 'bg-ice text-obsidian border-ice';
      case 'ERROR':
        return 'bg-red-500 text-white border-red-400';
      case 'WAKE_LISTENING':
        return 'bg-cyan/20 text-cyan border-cyan/40';
      default:
        return 'bg-navy-light text-muted border-white/10';
    }
  };

  return (
    <header className="h-16 frosted-glass border-b border-cyan/15 px-6 flex items-center justify-between z-10 bg-obsidian-darker/60 select-none">
      {/* State & connection badges */}
      <div className="flex items-center space-x-4">
        {/* Connection status */}
        <div className="flex items-center space-x-2">
          <div
            className={`w-2 h-2 rounded-full ${
              isBackendConnected ? 'bg-cyan shadow-cyan-glow animate-pulse' : 'bg-red-500'
            }`}
          />
          <span className="text-xs font-mono text-muted tracking-wider">
            {isBackendConnected ? 'CORE ONLINE' : 'DISCONNECTED'}
          </span>
        </div>

        {/* Dynamic state badge */}
        <div
          className={`px-3 py-1 rounded-full text-xs font-mono font-bold tracking-wider border uppercase transition-all ${getStateColor(
            state
          )}`}
        >
          {state.replace('_', ' ')}
        </div>
      </div>

      {/* Action toggles */}
      <div className="flex items-center space-x-4">
        <button onClick={onEnterFocus} className="text-xs text-cyan hover:text-white">Assistant view</button>
        <button onClick={onOpenSettings} className="text-xs text-cyan hover:text-white">Settings</button>
        {/* Auto-Conversation Mode (Continuous Talk) */}
        <div className="flex items-center space-x-2.5 bg-navy/60 px-3 py-1.5 rounded-xl border border-cyan/20">
          <MessageSquareCode className={`w-3.5 h-3.5 ${autoConversation ? 'text-cyan animate-pulse' : 'text-muted'}`} />
          <div className="flex flex-col">
            <span className="text-[11px] font-semibold text-white tracking-wide">
              Auto Conversation
            </span>
            <span className="text-[9px] font-mono text-muted">
              {autoConversation ? 'Active (Continuous)' : 'Manual Click'}
            </span>
          </div>
          <button
            type="button"
            onClick={onToggleAutoConversation}
            className={`w-9 h-5 rounded-full transition-colors relative p-0.5 ${
              autoConversation ? 'bg-cyan' : 'bg-navy-light'
            }`}
          >
            <div
              className={`w-4 h-4 rounded-full bg-obsidian transition-transform ${
                autoConversation ? 'translate-x-4' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* Wake Word ("Hey Oska") Switch */}
        <div className="flex items-center space-x-2.5 bg-navy/60 px-3 py-1.5 rounded-xl border border-cyan/20">
          <Radio className={`w-3.5 h-3.5 ${wakeWordEnabled ? 'text-cyan animate-pulse' : 'text-muted'}`} />
          <div className="flex flex-col">
            <span className="text-[11px] font-semibold text-white tracking-wide">
              Hey Oska
            </span>
            <span className="text-[9px] font-mono text-muted">
              {wakeWordEnabled ? `Active (${wakeWordStatus})` : 'Disabled'}
            </span>
          </div>
          <button
            type="button"
            onClick={onToggleWakeWord}
            className={`w-9 h-5 rounded-full transition-colors relative p-0.5 ${
              wakeWordEnabled ? 'bg-cyan' : 'bg-navy-light'
            }`}
          >
            <div
              className={`w-4 h-4 rounded-full bg-obsidian transition-transform ${
                wakeWordEnabled ? 'translate-x-4' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* Low Power Mode Toggle */}
        <button
          type="button"
          onClick={onToggleLowPower}
          title="Toggle Low-Power Graphics Mode"
          className={`p-2 rounded-xl border text-xs flex items-center space-x-1.5 transition-all ${
            lowPowerMode
              ? 'bg-violet/20 border-violet/40 text-ice'
              : 'bg-navy/40 border-cyan/15 text-muted hover:text-white'
          }`}
        >
          <Zap className="w-3.5 h-3.5" />
          <span className="hidden sm:inline font-mono text-[11px]">
            {lowPowerMode ? 'ECO' : 'PERF'}
          </span>
        </button>
      </div>
    </header>
  );
};
