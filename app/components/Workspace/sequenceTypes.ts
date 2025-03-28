export interface SequenceStep {
  id: string;
  step: number;
  day: number;
  channel: string;
  subject?: string;
  message: string;
  timing: string;
}

export interface SequenceData {
  id?: string;
  title: string;
  target_role: string;
  industry: string;
  company?: string;
  steps: SequenceStep[];
} 
