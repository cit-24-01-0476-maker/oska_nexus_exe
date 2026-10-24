import React from 'react';
import { 
  Home, 
  MessageSquare, 
  Cpu, 
  Bell, 
  FileText, Mail, 
  Clock, 
  Settings 
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab }) => {
  const menuItems = [
    { id: 'home', label: 'Home', icon: Home },
    { id: 'chat', label: 'AI Chat', icon: MessageSquare },
    { id: 'automations', label: 'Automations', icon: Cpu },
    { id: 'reminders', label: 'Reminders', icon: Bell },
    { id: 'notes', label: 'Notes', icon: FileText },
    { id: 'email', label: 'Email Draft', icon: Mail },
    { id: 'history', label: 'Audit Logs', icon: Clock },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 h-full frosted-glass border-r border-cyan/15 flex flex-col justify-between p-4 shrink-0 bg-obsidian-darker/80 z-20">
      <div>
        {/* Brand identity */}
        <div className="flex items-center space-x-3 px-2 py-3 mb-6 border-b border-cyan/15">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan via-ice to-violet flex items-center justify-center shadow-cyan-glow p-0.5">
            <div className="w-full h-full bg-obsidian rounded-[10px] flex items-center justify-center font-bold text-cyan text-sm font-mono">
              ON
            </div>
          </div>
          <div>
            <div className="text-sm font-bold tracking-wider text-white flex items-center space-x-1.5">
              <span>OSKA NEXUS</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan/15 text-cyan border border-cyan/30">
                v1.1
              </span>
            </div>
            <div className="text-[11px] text-muted tracking-tight">Obsidian Intelligence</div>
          </div>
        </div>

        {/* Navigation list */}
        <nav className="space-y-1.5">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-cyan/15 text-cyan border border-cyan/40 shadow-cyan-glow font-semibold'
                    : 'text-muted hover:text-white hover:bg-white/5 border border-transparent'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan' : 'text-muted'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer shortcut pill */}
      <div className="p-3 rounded-xl bg-navy/50 border border-cyan/15 text-[11px] text-muted space-y-1">
        <div className="text-white font-medium flex items-center justify-between">
          <span>Global Shortcut</span>
          <kbd className="px-1.5 py-0.5 rounded bg-navy-light border border-cyan/30 text-cyan text-[10px] font-mono">
            Ctrl+Shift+Space
          </kbd>
        </div>
        <p className="text-[10px] leading-tight text-muted">
          Activate floating assistant instantly over any application.
        </p>
      </div>
    </aside>
  );
};

