import React, { useState, useEffect } from 'react';
import { Clock, ShieldCheck } from 'lucide-react';
import { api } from '../services/api';

export const HistoryPage: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [error, setError] = useState('');



  async function loadLogs() {
    try {
      const data = await api.getAudit();
      setLogs(data);
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  };

  useEffect(() => {
  // eslint-disable-next-line react/set-state-in-effect -- Loads backend data asynchronously.
    loadLogs();
  }, []);

  return (
    <div className="flex-1 flex flex-col h-full bg-obsidian p-6 overflow-y-auto">
      <div className="flex items-center justify-between pb-4 border-b border-cyan/15 mb-6">
        <div>
          <h2 className="text-lg font-bold text-white tracking-wide flex items-center space-x-2">
            <Clock className="w-5 h-5 text-cyan" />
            <span>SECURITY & AUDIT LOGS</span>
          </h2>
          <p className="text-xs text-muted">
            Transparent, unredacted audit trail of all commands and actions executed by OSKA NEXUS.
          </p>
        </div>
        <div className="flex items-center space-x-1.5 text-xs text-cyan font-mono">
          <ShieldCheck className="w-4 h-4" />
          <span>SECURITY MONITOR ACTIVE</span>
        </div>
      </div>

      {error && <p role="alert" className="text-red-400 text-sm">{error}</p>}
      <div className="space-y-2">
        {logs.length === 0 ? (
          <div className="text-center py-12 text-muted text-xs">
            No activity logged yet.
          </div>
        ) : (
          logs.map((log) => (
            <div
              key={log.id}
              className="frosted-glass rounded-xl p-3 border border-cyan/15 bg-navy/30 flex items-center justify-between text-xs font-mono"
            >
              <div className="flex items-center space-x-3">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  log.status === 'SUCCESS' ? 'bg-cyan/15 text-cyan' : 'bg-violet/20 text-violet'
                }`}>
                  {log.status}
                </span>
                <span className="text-white font-sans">{log.details}</span>
              </div>
              <div className="flex items-center space-x-4 text-muted text-[11px]">
                {log.action_type && (
                  <span className="text-cyan/70">[{log.action_type}]</span>
                )}
                <span>
                  {new Date(log.created_at * 1000).toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
