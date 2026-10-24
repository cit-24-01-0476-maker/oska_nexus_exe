import React, { useState, useEffect } from 'react';
import { Play, Plus, Cpu, ArrowRight } from 'lucide-react';
import { Routine } from '../types/assistant';
import { api } from '../services/api';

export const AutomationsPage: React.FC = () => {
  const [routines, setRoutines] = useState<Routine[]>([]);
  const [executingId, setExecutingId] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<any | null>(null);
  const [showBuilder, setShowBuilder] = useState(false);

  // New routine builder form state
  const [newId, setNewId] = useState('');
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newTrigger, setNewTrigger] = useState('');
  const [newActionType, setNewActionType] = useState('open_app');
  const [newActionTarget, setNewActionTarget] = useState('');
  const [steps, setSteps] = useState<{ type: string; target: string; label: string }[]>([]);

  useEffect(() => {
    loadRoutines();
  }, []);

  async function loadRoutines() {
    try {
      const data = await api.getRoutines();
      setRoutines(data);
    } catch (e) { setLastResult({ status: 'FAILED', response: e instanceof Error ? e.message : String(e) }); }
  };

  const handleRun = async (id: string) => {
    setExecutingId(id);
    try {
      const res = await api.runRoutine(id);
      setLastResult(res);
    } catch {
      setLastResult({ status: 'FAILED', response: 'Failed to run routine' });
    } finally {
      setExecutingId(null);
    }
  };

  const handleCreateRoutine = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newId || !newName) return;

    try {
      await api.createRoutine({
        id: newId.trim().toLowerCase().replace(/\s+/g, '-'), name: newName.trim(), description: newDesc,
        trigger_phrase: newTrigger.trim(), actions: [...steps, ...(newActionTarget.trim() ? [{ type: newActionType, target: newActionTarget.trim(), label: `${newActionType}: ${newActionTarget.trim()}` }] : [])],
      });
    } catch (e) { setLastResult({ status: 'FAILED', response: e instanceof Error ? e.message : String(e) }); return; }
    setShowBuilder(false);
    setNewId('');
    setNewName('');
    setNewDesc('');
    setNewTrigger('');
    setNewActionTarget('');
    setSteps([]);
    loadRoutines();
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-obsidian p-6 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-cyan/15 mb-6">
        <div>
          <h2 className="text-lg font-bold text-white tracking-wide flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-cyan" />
            <span>SMART AUTOMATION ENGINE</span>
          </h2>
          <p className="text-xs text-muted">
            Chain desktop actions, applications, audio configurations, and timers into voice-triggered routines.
          </p>
        </div>
        <button
          onClick={() => setShowBuilder(!showBuilder)}
          className="px-4 py-2 rounded-xl bg-cyan hover:bg-cyan/80 text-obsidian text-xs font-bold transition-all flex items-center space-x-1.5 shadow-cyan-glow"
        >
          <Plus className="w-4 h-4" />
          <span>New Routine</span>
        </button>
      </div>

      {/* Routine Builder Modal */}
      {showBuilder && (
        <form
          onSubmit={handleCreateRoutine}
          className="mb-6 p-5 rounded-2xl frosted-glass border border-cyan/30 bg-navy/80 space-y-4"
        >
          <div className="text-sm font-bold text-white flex items-center space-x-2">
            <Plus className="w-4 h-4 text-cyan" />
            <span>CREATE CUSTOM ROUTINE</span>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-muted block mb-1">Routine ID</label>
              <input
                type="text"
                value={newId}
                onChange={(e) => setNewId(e.target.value)}
                placeholder="e.g. routine-gaming"
                required
                className="w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-xs text-white"
              />
            </div>
            <div>
              <label className="text-xs text-muted block mb-1">Display Name</label>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="e.g. Gaming Mode"
                required
                className="w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-xs text-white"
              />
            </div>
          </div>
          <div>
            <label className="text-xs text-muted block mb-1">Description</label>
            <input
              type="text"
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              placeholder="What this routine accomplishes..."
              className="w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-xs text-white"
            />
          </div>
          <div>
            <label className="text-xs text-muted block mb-1">Voice Trigger Phrase</label>
            <input
              type="text"
              value={newTrigger}
              onChange={(e) => setNewTrigger(e.target.value)}
              placeholder="e.g. gaming mode"
              className="w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-xs text-white"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-muted block mb-1">Action Type</label>
              <select
                value={newActionType}
                onChange={(e) => setNewActionType(e.target.value)}
                className="w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-xs text-white"
              >
                <option value="open_app">Launch Application</option>
                <option value="open_url">Open Web URL</option>
                <option value="set_volume">Set Audio Volume (%)</option>
                <option value="notify">Desktop Notification</option>
                <option value="timer">Focus Timer (minutes)</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-muted block mb-1">Target</label>
              <input
                type="text"
                value={newActionTarget}
                onChange={(e) => setNewActionTarget(e.target.value)}
                placeholder="e.g. notepad, https://google.com, 50"
                required={!steps.length}
                className="w-full bg-obsidian border border-cyan/20 rounded-xl px-3 py-2 text-xs text-white"
              />
            </div>
          </div>
          <button type="button" disabled={!newActionTarget.trim()} className="text-xs text-cyan disabled:opacity-40" onClick={() => { setSteps([...steps, { type: newActionType, target: newActionTarget.trim(), label: `${newActionType}: ${newActionTarget.trim()}` }]); setNewActionTarget(''); }}>+ Add another step</button>
          {steps.map((step, index) => <div key={index} className="flex gap-3 text-xs"><span>{index + 1}. {step.label}</span><button type="button" className="text-red-400" onClick={() => setSteps(steps.filter((_, i) => i !== index))}>Remove step</button></div>)}
          <div className="flex justify-end space-x-2 pt-2">
            <button
              type="button"
              onClick={() => setShowBuilder(false)}
              className="px-4 py-1.5 rounded-xl border border-white/10 text-xs text-muted hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-1.5 rounded-xl bg-cyan text-obsidian text-xs font-bold shadow-cyan-glow"
            >
              Save Routine
            </button>
          </div>
        </form>
      )}

      {lastResult && <p role="status" className={`text-sm mb-4 ${lastResult.status === 'FAILED' ? 'text-red-400' : 'text-cyan'}`}>{lastResult.response}</p>}
      {/* Routine Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {routines.map((r) => {
          const isRunning = executingId === r.id;
          return (
            <div
              key={r.id}
              className="frosted-glass rounded-2xl p-5 border border-cyan/20 hover:border-cyan/40 transition-all flex flex-col justify-between space-y-4 bg-navy/40"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-bold text-white tracking-wide">{r.name}</h3>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-cyan/15 text-cyan border border-cyan/30">
                    Voice: "{r.trigger_phrase}"
                  </span>
                </div>
                <p className="text-xs text-muted leading-relaxed mb-4">{r.description}</p>

                {/* Steps */}
                <div className="space-y-1.5 bg-obsidian-darker/60 rounded-xl p-3 border border-cyan/10">
                  <div className="text-[10px] font-mono text-cyan uppercase mb-1">
                    Configured Steps ({r.actions.length}):
                  </div>
                  {r.actions.map((act, i) => (
                    <div
                      key={i}
                      className="text-xs text-white/80 flex items-center space-x-2 font-mono"
                    >
                      <ArrowRight className="w-3 h-3 text-cyan/70 shrink-0" />
                      <span>{act.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  onClick={() => handleRun(r.id)}
                  disabled={isRunning}
                  className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center space-x-2 transition-all ${
                    isRunning
                      ? 'bg-cyan text-obsidian animate-pulse'
                      : 'bg-cyan/15 hover:bg-cyan text-cyan hover:text-obsidian border border-cyan/30'
                  }`}
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>{isRunning ? 'Executing Steps...' : 'Run Routine'}</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
