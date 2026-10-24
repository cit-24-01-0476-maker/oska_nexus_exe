import React, { useState, useEffect } from 'react';
import { Activity, Cpu, HardDrive, Play, CheckCircle2 } from 'lucide-react';
import { SystemMetrics, Routine } from '../types/assistant';
import { api } from '../services/api';
import { wsClient } from '../services/websocket';

interface RightPanelProps {
  onRunRoutine: (id: string) => Promise<any>;
}

export const RightPanel: React.FC<RightPanelProps> = ({ onRunRoutine }) => {
  const [result, setResult] = useState('');
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [routines, setRoutines] = useState<Routine[]>([]);
  const [runningRoutineId, setRunningRoutineId] = useState<string | null>(null);



  async function fetchMetrics() {
    try {
      const data = await api.getMetrics();
      setMetrics(data);
    } catch {
      // Backend starting up
    }
  };

  async function fetchRoutines() {
    try {
      const list = await api.getRoutines();
      setRoutines(list);
    } catch {}
  };

  useEffect(() => {
    // Initial fetch
  // eslint-disable-next-line react/set-state-in-effect -- Loads backend data asynchronously.
    fetchMetrics();
    fetchRoutines();

    // Poll metrics every 4s
    const timer = setInterval(fetchMetrics, 4000);
    const unsubscribe = wsClient.on('connection', ({ connected }) => {
      if (connected) { void fetchMetrics(); void fetchRoutines(); }
    });
    return () => { clearInterval(timer); unsubscribe(); };
  }, []);

  const handleRun = async (id: string) => {
    setRunningRoutineId(id);
    try { const result = await onRunRoutine(id); setResult(result.response); }
    catch (e) { setResult(e instanceof Error ? e.message : String(e)); }
    finally { setRunningRoutineId(null); }
  };

  return (
    <aside className="w-80 h-full frosted-glass border-l border-cyan/15 p-5 flex flex-col justify-between shrink-0 bg-obsidian-darker/70 overflow-y-auto">
      <div className="space-y-6">
        {result && <p role="status" className="text-xs text-cyan">{result}</p>}
        {/* System Intelligence Panel */}
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono font-semibold tracking-wider text-cyan mb-3">
            <Activity className="w-4 h-4 text-cyan" />
            <span>SYSTEM METRICS</span>
          </div>

          {metrics ? (
            <div className="space-y-3 bg-navy/40 rounded-2xl p-4 border border-cyan/15">
              {/* CPU */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-muted flex items-center space-x-1.5">
                    <Cpu className="w-3.5 h-3.5 text-cyan" />
                    <span>CPU ({metrics.cpu.cores} Cores)</span>
                  </span>
                  <span className="font-mono text-white font-semibold">
                    {metrics.cpu.percent}%
                  </span>
                </div>
                <div className="h-1.5 w-full bg-navy-light rounded-full overflow-hidden">
                  <div
                    className="h-full bg-cyan rounded-full transition-all duration-500"
                    style={{ width: `${metrics.cpu.percent}%` }}
                  />
                </div>
              </div>

              {/* RAM */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-muted flex items-center space-x-1.5">
                    <HardDrive className="w-3.5 h-3.5 text-violet" />
                    <span>RAM ({metrics.ram.used_gb} / {metrics.ram.total_gb} GB)</span>
                  </span>
                  <span className="font-mono text-white font-semibold">
                    {metrics.ram.percent}%
                  </span>
                </div>
                <div className="h-1.5 w-full bg-navy-light rounded-full overflow-hidden">
                  <div
                    className="h-full bg-violet rounded-full transition-all duration-500"
                    style={{ width: `${metrics.ram.percent}%` }}
                  />
                </div>
              </div>

              {/* Disk & Battery info */}
              <div className="pt-2 border-t border-cyan/10 grid grid-cols-2 gap-2 text-[11px]">
                <div>
                  <span className="text-muted block">Storage (C:)</span>
                  <span className="font-mono text-white">
                    {metrics.disk.free_gb} GB Free
                  </span>
                </div>
                <div>
                  <span className="text-muted block">Uptime</span>
                  <span className="font-mono text-white">{metrics.uptime}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-xs text-muted font-mono p-4 bg-navy/20 rounded-2xl border border-cyan/10">
              Gathering hardware telemetry...
            </div>
          )}
        </div>

        {/* Quick Automations */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono font-semibold tracking-wider text-cyan">
              QUICK ROUTINES
            </span>
            <span className="text-[10px] font-mono text-muted">
              {routines.length} ACTIVE
            </span>
          </div>

          <div className="space-y-2">
            {routines.map((r) => {
              const isRunning = runningRoutineId === r.id;
              return (
                <div
                  key={r.id}
                  className="bg-navy/50 rounded-xl p-3 border border-cyan/15 hover:border-cyan/40 transition-all flex items-center justify-between"
                >
                  <div>
                    <div className="text-xs font-semibold text-white">{r.name}</div>
                    <div className="text-[10px] text-muted truncate max-w-[170px]">
                      {r.description}
                    </div>
                  </div>
                  <button
                    onClick={() => handleRun(r.id)}
                    disabled={isRunning}
                    className={`w-7 h-7 rounded-lg flex items-center justify-center transition-all ${
                      isRunning
                        ? 'bg-cyan text-obsidian shadow-cyan-glow'
                        : 'bg-cyan/10 text-cyan hover:bg-cyan hover:text-obsidian'
                    }`}
                  >
                    {isRunning ? (
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    ) : (
                      <Play className="w-3.5 h-3.5 fill-current" />
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Security notice footer */}
      <div className="p-3 rounded-xl bg-obsidian-card border border-cyan/10 text-[10px] text-muted space-y-1">
        <div className="text-cyan font-mono font-semibold flex items-center space-x-1">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan inline-block" />
          <span>LOCAL DESKTOP CORE</span>
        </div>
        <p className="leading-relaxed">
          Desktop commands run on this PC. Shutdown and restart require confirmation.
        </p>
      </div>
    </aside>
  );
};
