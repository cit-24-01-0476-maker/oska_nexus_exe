import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Sparkles, 
  Mic, 
  Volume2, 
  Radio, 
  Cpu, 
  Monitor, 
  ArrowRight, 
  CheckCircle2, 
  Play 
} from 'lucide-react';
import { api } from '../services/api';

interface OnboardingModalProps {
  onComplete: () => void;
}

export const OnboardingModal: React.FC<OnboardingModalProps> = ({ onComplete }) => {
  const [step, setStep] = useState(1);
  const [micTested, setMicTested] = useState(false);
  const [voiceTested, setVoiceTested] = useState(false);
  const [isExecutingTest, setIsExecutingTest] = useState(false);

  const handleTestVoice = async () => {
    try {
      await api.testVoice();
      setVoiceTested(true);
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const handleTestMic = async () => {
    try {
      await api.startListening();
      setMicTested(true);
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const handleTestCommand = async () => {
    setIsExecutingTest(true);
    try {
      await api.sendCommand('What time is it?');
      onComplete();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    } finally {
      setIsExecutingTest(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-obsidian-darker/90 backdrop-blur-2xl select-none">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-xl frosted-glass rounded-3xl border border-cyan/40 p-8 shadow-cyan-glow bg-obsidian-card relative overflow-hidden"
      >
        {/* Step indicator & Skip */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-cyan/15">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan animate-pulse shadow-cyan-glow" />
            <span className="text-xs font-mono font-bold text-cyan tracking-wider">
              SETUP WIZARD • STEP {step} OF 9
            </span>
          </div>
          <button
            onClick={onComplete}
            className="text-xs text-muted hover:text-cyan transition-colors font-mono"
            title="Skip onboarding"
          >
            Skip to Dashboard &rarr;
          </button>
        </div>

        {/* Step Contents */}
        <div className="min-h-[220px] flex flex-col justify-center">
          {step === 1 && (
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-cyan/10 border border-cyan/30 flex items-center justify-center text-cyan shadow-cyan-glow">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white tracking-wide">
                Welcome to OSKA NEXUS
              </h3>
              <p className="text-sm text-muted leading-relaxed">
                Your personal holographic desktop intelligence. OSKA connects your voice, natural language reasoning, and native Windows automation into an ultra-responsive JARVIS-style assistant.
              </p>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-cyan/10 border border-cyan/30 flex items-center justify-center text-cyan">
                <Mic className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white">Target Microphone</h3>
              <p className="text-xs text-muted">
                OSKA uses Faster-Whisper for local offline speech recognition. The default system microphone is selected automatically.
              </p>
              <div className="p-3 bg-navy/60 rounded-xl border border-cyan/20 text-xs text-ice">
                The default microphone will be checked when you run the microphone test.
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-cyan/10 border border-cyan/30 flex items-center justify-center text-cyan">
                <Mic className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white">Test Microphone Input</h3>
              <p className="text-xs text-muted">
                Click below to start a test recording. Speak into your microphone to verify speech capture.
              </p>
              <button
                type="button"
                onClick={handleTestMic}
                className="px-4 py-2.5 rounded-xl bg-cyan/20 hover:bg-cyan/30 text-cyan border border-cyan/40 text-xs font-bold flex items-center space-x-2"
              >
                <Mic className="w-4 h-4" />
                <span>{micTested ? 'Recording Requested' : 'Trigger Audio Capture Test'}</span>
              </button>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-cyan/10 border border-cyan/30 flex items-center justify-center text-cyan">
                <Volume2 className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white">Voice Output (TTS)</h3>
              <p className="text-xs text-muted">
                Test the Windows text-to-speech engine. Listen to verify clear voice synthesis.
              </p>
              <button
                type="button"
                onClick={handleTestVoice}
                className="px-4 py-2.5 rounded-xl bg-cyan text-obsidian text-xs font-bold flex items-center space-x-2 shadow-cyan-glow"
              >
                <Play className="w-4 h-4 fill-current" />
                <span>{voiceTested ? 'Test Voice Requested' : 'Play Test Voice'}</span>
              </button>
            </div>
          )}

          {step === 5 && (
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-cyan/10 border border-cyan/30 flex items-center justify-center text-cyan">
                <Radio className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white">Hands-Free "Hey Oska"</h3>
              <p className="text-xs text-muted leading-relaxed">
                OSKA supports Picovoice Porcupine wake-word detection. You can enter an AccessKey and a custom Hey Oska .ppn model in Settings to enable hands-free voice invocation, or use the global hotkey <kbd className="text-cyan font-mono px-1 py-0.5 bg-navy-light rounded">Ctrl+Shift+Space</kbd> anytime.
              </p>
            </div>
          )}

          {step === 6 && (
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-cyan/10 border border-cyan/30 flex items-center justify-center text-cyan">
                <Cpu className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white">AI Intelligence Layer</h3>
              <p className="text-xs text-muted leading-relaxed">
                Desktop commands run locally. Online speech recognition is tried first, with local Whisper as fallback; neural voices need internet. You can also connect Ollama, OpenAI, or Google Gemini in Settings for advanced conversation.
              </p>
            </div>
          )}

          {step === 7 && (
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-cyan/10 border border-cyan/30 flex items-center justify-center text-cyan">
                <Monitor className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white">Background Tray Assistant</h3>
              <p className="text-xs text-muted leading-relaxed">
                Closing the main window minimizes OSKA to the Windows notification area tray, keeping your routines, shortcuts, and wake-word ready at all times.
              </p>
            </div>
          )}

          {step === 8 && (
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-cyan/10 border border-cyan/30 flex items-center justify-center text-cyan">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white">Windows Login Integration</h3>
              <p className="text-xs text-muted leading-relaxed">
                By default, OSKA starts only when you launch it. You can optionally toggle automatic startup in Settings.
              </p>
            </div>
          )}

          {step === 9 && (
            <div className="space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-cyan/10 border border-cyan/30 flex items-center justify-center text-cyan shadow-cyan-glow">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white">Execute Your First Command</h3>
              <p className="text-xs text-muted leading-relaxed">
                Click below to have OSKA inspect the system clock and announce the time, or click Open OSKA NEXUS to enter directly!
              </p>
              <div className="flex flex-wrap gap-3 pt-2">
                <button
                  type="button"
                  onClick={handleTestCommand}
                  disabled={isExecutingTest}
                  className="px-5 py-3 rounded-xl bg-cyan hover:bg-cyan/80 text-obsidian text-xs font-bold flex items-center space-x-2 shadow-cyan-glow transition-all"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span>{isExecutingTest ? 'Checking Time...' : 'Run "What time is it?"'}</span>
                </button>
                <button
                  type="button"
                  onClick={onComplete}
                  className="px-5 py-3 rounded-xl bg-navy-light hover:bg-white/10 text-white text-xs font-bold border border-cyan/30 transition-all"
                >
                  Enter Dashboard Directly &rarr;
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Navigation buttons */}
        <div className="flex justify-between items-center mt-8 pt-4 border-t border-cyan/15">
          {step > 1 ? (
            <button
              type="button"
              onClick={() => setStep(step - 1)}
              className="text-xs text-muted hover:text-white px-3 py-1.5"
            >
              Back
            </button>
          ) : (
            <div />
          )}

          {step < 9 ? (
            <button
              type="button"
              onClick={() => setStep(step + 1)}
              className="px-5 py-2 rounded-xl bg-cyan hover:bg-cyan/80 text-obsidian text-xs font-bold flex items-center space-x-1.5 shadow-cyan-glow"
            >
              <span>Next</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          ) : (
            <button
              type="button"
              onClick={onComplete}
              className="px-6 py-2 rounded-xl bg-gradient-to-r from-cyan to-violet text-white text-xs font-bold flex items-center space-x-1.5 shadow-cyan-glow hover:opacity-90 transition-all"
            >
              <span>Open OSKA NEXUS</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </motion.div>
    </div>
  );
};
