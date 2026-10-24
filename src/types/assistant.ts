export type AssistantState = 
  | 'STOPPED'
  | 'IDLE'
  | 'WAKE_LISTENING'
  | 'WAKE_DETECTED'
  | 'LISTENING'
  | 'TRANSCRIBING'
  | 'THINKING'
  | 'AWAITING_CONFIRMATION'
  | 'EXECUTING'
  | 'SPEAKING'
  | 'SUCCESS'
  | 'ERROR';

export interface AssistantContext {
  last_error?: string | null;
  transcript?: string;
  response?: string;
  pending_confirmation?: string | null;
  waveform_level?: number;
  timestamp?: number;
}

export interface SystemMetrics {
  os: string;
  cpu: {
    percent: number;
    cores: number;
  };
  ram: {
    percent: number;
    used_gb: number;
    total_gb: number;
  };
  battery: {
    has_battery: boolean;
    percent: number | null;
    power_plugged: boolean | null;
  };
  disk: {
    percent: number;
    free_gb: number;
    total_gb: number;
  };
  uptime: string;
}

export interface RoutineStep {
  type: string;
  target: string;
  label: string;
}

export interface Routine {
  id: string;
  name: string;
  description: string;
  trigger_phrase: string;
  actions: RoutineStep[];
  enabled: number;
  created_at: number;
}

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  command_intent?: string;
  status?: string;
  created_at: number;
}

export interface AudioDevice {
  id: number;
  name: string;
  channels: number;
  default: boolean;
}

export interface TTSVoice {
  id: string;
  name: string;
  languages: string[];
  gender: string;
}
