import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { RightPanel } from './components/RightPanel';
import { HomePage } from './pages/HomePage';
import { FocusedAssistantPage } from './pages/FocusedAssistantPage';
import { EmailPage } from './pages/EmailPage';
import { ChatPage } from './pages/ChatPage';
import { AutomationsPage } from './pages/AutomationsPage';
import { RemindersPage } from './pages/RemindersPage';
import { NotesPage } from './pages/NotesPage';
import { HistoryPage } from './pages/HistoryPage';
import { SettingsPage } from './pages/SettingsPage';
import { OnboardingModal } from './pages/OnboardingModal';
import { FloatingOrb } from './overlay/FloatingOrb';
import { AssistantState } from './types/assistant';
import { wsClient } from './services/websocket';
import { api } from './services/api';

export function App() {
  return new URLSearchParams(window.location.search).get('overlay') === 'true' ? <FloatingOrb /> : <Dashboard />;
}

function Dashboard() {
  // Main Dashboard State
  const [currentTab, setCurrentTab] = useState('home');
  const [focusMode, setFocusMode] = useState(() => localStorage.getItem('oska_assistant_view') !== 'dashboard');
  const setFocus = (focused: boolean) => { setFocusMode(focused); localStorage.setItem('oska_assistant_view', focused ? 'focus' : 'dashboard'); };
  const [state, setState] = useState<AssistantState>('IDLE');
  const [waveformLevel, setWaveformLevel] = useState(0);
  const [lowPowerMode, setLowPowerMode] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [pendingConfirmation, setPendingConfirmation] = useState<any | null>(null);
  const [wakeWordEnabled, setWakeWordEnabled] = useState(false);
  const [autoConversation, setAutoConversation] = useState(false);
  const [aiProvider, setAiProvider] = useState('local_rules');
  const [wakeWordStatus, setWakeWordStatus] = useState('UNINITIALIZED');
  const [isBackendConnected, setIsBackendConnected] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(() => !localStorage.getItem('oska_nexus_onboarding_completed'));

  useEffect(() => {
    // Check first-run onboarding

    // Initial state fetch
    api.getState().then((data) => {
      setState(data.state);
      setWakeWordStatus(data.wake_status);
      setIsBackendConnected(true);
      setTranscript(data.context?.transcript || '');
      setResponse(data.context?.response || '');
      setPendingConfirmation(data.context?.pending_confirmation || null);
    }).catch(() => {
      setIsBackendConnected(false);
    });

    api.getSettings().then((st) => {
      setWakeWordEnabled(st.wake_word_enabled === 'true');
      setLowPowerMode(st.low_power_mode === 'true');
      setAiProvider(st.llm_provider || 'local_rules');
      setAutoConversation(st.auto_conversation === 'true');
    }).catch(() => {});

    // WebSocket Listeners
    const applySnapshot = (data: any) => {
      setState(data.state);
      setWakeWordStatus(data.wake_status);
      setTranscript(data.context?.transcript || '');
      setResponse(data.context?.response || '');
      setPendingConfirmation(data.context?.pending_confirmation || null);
    };
    const unsubInitial = wsClient.on('initial_state', applySnapshot);
    const unEmail = wsClient.on('email_draft_changed', () => setCurrentTab('email'));
    const unsubSettings = wsClient.on('settings_changed', ({ settings: st }) => {
      setWakeWordEnabled(st.wake_word_enabled === 'true');
      setAutoConversation(st.auto_conversation === 'true');
      setLowPowerMode(st.low_power_mode === 'true');
      setAiProvider(st.llm_provider || 'local_rules');
    });
    const unsubDetected = wsClient.on('wake_detected', () => {
      if ((window as any).__TAURI_INTERNALS__) import('@tauri-apps/api/core').then(({ invoke }) => invoke('reveal_floating_assistant')).catch(console.error);
    });
    const unsubWake = wsClient.on('wake_status', (data) => setWakeWordStatus(data.status));
    const unNotify = wsClient.on('notification', (data) => {
      setResponse(data.body);
      if ((window as any).__TAURI_INTERNALS__) import('@tauri-apps/api/core').then(({ invoke }) => invoke('notify_user', { title: data.title, body: data.body })).catch(console.error);
    });
    const unsubReminder = wsClient.on('reminder_due', (data) => {
      setResponse(`Reminder: ${data.reminder.title}`);
      if ((window as any).__TAURI_INTERNALS__) import('@tauri-apps/api/core').then(({ invoke }) => invoke('notify_user', { title: 'OSKA Reminder', body: data.reminder.title })).catch(console.error);
    });
    const unsubConn = wsClient.on('connection', (data) => {
      setIsBackendConnected(data.connected);
      if (data.connected) api.getSettings().then(st => {
        setWakeWordEnabled(st.wake_word_enabled === 'true');
        setAutoConversation(st.auto_conversation === 'true');
        setLowPowerMode(st.low_power_mode === 'true');
      setAiProvider(st.llm_provider || 'local_rules');
      }).catch(console.error);
    });

    const unsubState = wsClient.on('state_change', (data) => {
      setState(data.state);
      if (data.context) {
        if (data.context.transcript !== undefined) setTranscript(data.context.transcript);
        if (data.context.response !== undefined) setResponse(data.context.response);
        if (data.context.pending_confirmation) {
          setPendingConfirmation(data.context.pending_confirmation);
        } else {
          setPendingConfirmation(null);
        }
      }
    });

    const unsubWave = wsClient.on('waveform', (data) => {
      setWaveformLevel(data.level || 0);
    });

    const unsubCmd = wsClient.on('command_result', (data) => {
      if (data.result) {
        setResponse(data.result.response || '');
        if (data.result.status === 'REQUIRES_CONFIRMATION') {
          setPendingConfirmation(data.result.data);
        }
      }
    });

    return () => {
      unNotify();
      unsubDetected();
      unEmail();
      unsubInitial();
      unsubSettings();
      unsubWake();
      unsubReminder();
      unsubConn();
      unsubState();
      unsubWave();
      unsubCmd();
    };
  }, []);

  const handleExecuteCommand = async (text: string) => {
    setTranscript(text);
    try {
      const res = await api.sendCommand(text);
      if (res.response) setResponse(res.response);
      if (res.status === 'REQUIRES_CONFIRMATION') {
        setPendingConfirmation(res.data);
      }
    } catch (e) {
      setResponse(e instanceof Error ? e.message : 'Connection error executing command.');
    }
  };

  const handleStartListening = async () => {
    try {
      await api.startListening();
    } catch (e) {
      setResponse(e instanceof Error ? e.message : String(e));
    }
  };

  const handleStopListening = async () => {
    try { await api.stopListening(); setAutoConversation(false); setResponse('Listening stopped.'); }
    catch (e) { setResponse(e instanceof Error ? e.message : String(e)); }
  };

  const handleToggleWakeWord = async () => {
    try {
      const res = await api.toggleWakeWord();
      setWakeWordEnabled(res.enabled);
      setWakeWordStatus(res.status);
    } catch (e) {
      setResponse(e instanceof Error ? e.message : String(e));
    }
  };

  const handleToggleAutoConversation = async () => {
    try {
      const res = await api.toggleAutoConversation();
      setAutoConversation(res.auto_conversation);
    } catch (e) {
      setResponse(e instanceof Error ? e.message : String(e));
    }
  };

  const handleToggleLowPower = () => {
    const next = !lowPowerMode;
    setLowPowerMode(next);
    api.updateSettings({ low_power_mode: next ? 'true' : 'false' }).catch((e) => { setLowPowerMode(!next); setResponse(e.message); });
  };

  const handleConfirmAction = async (action: string, confirmed: boolean) => {
    try {
      const result = await api.confirmPowerAction(action, confirmed);
      setResponse(result.message);
      setPendingConfirmation(null);
    } catch (e) { setResponse(e instanceof Error ? e.message : String(e)); }
  };

  const handleCompleteOnboarding = () => {
    localStorage.setItem('oska_nexus_onboarding_completed', 'true');
    setShowOnboarding(false);
  };

  return (
    <div className="w-screen h-screen flex flex-col bg-obsidian text-white overflow-hidden select-none">
      {focusMode ? <FocusedAssistantPage state={state} waveformLevel={waveformLevel} lowPowerMode={lowPowerMode} transcript={transcript} response={response} connected={isBackendConnected} aiProvider={aiProvider} onAISettings={() => { setFocus(false); setCurrentTab('settings'); }} autoConversation={autoConversation} onListen={handleStartListening} onStop={handleStopListening} onToggleConversation={handleToggleAutoConversation} onCommand={handleExecuteCommand} onDashboard={() => setFocus(false)} /> : <>
      {/* Top Cybernetic Status Header */}
      <Header
        state={state}
        wakeWordEnabled={wakeWordEnabled}
        wakeWordStatus={wakeWordStatus}
        onToggleWakeWord={handleToggleWakeWord}
        autoConversation={autoConversation}
        onToggleAutoConversation={handleToggleAutoConversation}
        lowPowerMode={lowPowerMode}
        onToggleLowPower={handleToggleLowPower}
        onOpenSettings={() => setCurrentTab('settings')}
        onEnterFocus={() => setFocus(true)}
        isBackendConnected={isBackendConnected}
      />

      {/* Main Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar currentTab={currentTab} onSelectTab={setCurrentTab} />

        {/* Center Content View */}
        <main className="flex-1 flex flex-col overflow-hidden relative">
          {currentTab === 'home' && (
            <HomePage
              state={state}
              waveformLevel={waveformLevel}
              lowPowerMode={lowPowerMode}
              transcript={transcript}
              response={response}
              onExecuteCommand={handleExecuteCommand}
              onStartListening={handleStartListening}
              pendingConfirmation={null}
              onConfirmAction={handleConfirmAction}
            />
          )}
          {currentTab === 'chat' && (
            <ChatPage onExecuteCommand={async (text) => { const res = await api.sendCommand(text); setTranscript(text); setResponse(res.response || ''); if (res.status === 'REQUIRES_CONFIRMATION') setPendingConfirmation(res.data); }} />
          )}
          {currentTab === 'automations' && <AutomationsPage />}
          {currentTab === 'reminders' && <RemindersPage />}
          {currentTab === 'notes' && <NotesPage />}
          {currentTab === 'email' && <EmailPage />}
          {currentTab === 'history' && <HistoryPage />}
          {currentTab === 'settings' && <SettingsPage />}
        </main>

        {/* Right Info and Quick Actions Panel (shown on home tab) */}
        {currentTab === 'home' && (
          <RightPanel onRunRoutine={(id) => api.runRoutine(id)} />
        )}
      </div>

      </>}
      {pendingConfirmation && <div role="dialog" aria-modal="true" aria-label="Confirm power action" className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-6">
        <div className="bg-navy border border-cyan/40 rounded-2xl p-6 space-y-4 max-w-md">
          <h2 className="text-lg font-bold">Confirm power action</h2><p>{response}</p>
          <p className="text-xs text-muted">Confirmation expires after 60 seconds.</p>
          <div className="flex gap-4"><button className="px-4 py-2 bg-red-600 rounded-lg" onClick={() => handleConfirmAction(pendingConfirmation.pending_action, true)}>Confirm</button><button className="px-4 py-2 border rounded-lg" onClick={() => handleConfirmAction(pendingConfirmation.pending_action, false)}>Cancel</button></div>
        </div>
      </div>}
      {/* First-Run Onboarding Modal */}
      {showOnboarding && (
        <OnboardingModal onComplete={handleCompleteOnboarding} />
      )}
    </div>
  );
}

export default App;
