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
  id?: string | number;
  title: string;
  target_role: string;
  industry: string;
  company?: string;
  steps: SequenceStep[];
}

export interface ApiResponse<T> {
  success: boolean;
  error?: string;
  data?: T;
}

export interface SequenceResponseData {
  sequence_data: SequenceData | null;
}

export interface SequenceResponse {
  success: boolean;
  error?: string;
  data?: SequenceResponseData;
}

export interface SequenceSaveResponse extends ApiResponse<{ sequence_id: number }> {
  sequence_id: number;
}

export interface SequenceResetResponse extends ApiResponse<{ reset: boolean }> {
  reset: boolean;
}

export interface SequenceErrorResponse {
  error: string;
  success: false;
} 
