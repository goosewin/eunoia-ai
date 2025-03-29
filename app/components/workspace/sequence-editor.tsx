import { AlertCircle, CheckCircle, Plus, Trash } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Button } from '../ui/button';
import { SequenceData, SequenceSaveResponse, SequenceStep } from './sequence-types';

export interface SequenceEditorProps {
  sequenceData: SequenceData;
  setSequenceData: (data: SequenceData | null) => void;
  sessionId: string | null;
}

export default function SequenceEditor({
  sequenceData,
  setSequenceData,
  sessionId
}: SequenceEditorProps) {
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const timeout = setTimeout(() => {
      if (saveStatus !== 'idle') {
        setSaveStatus('idle');
        setErrorMessage(null);
      }
    }, 3000);

    return () => clearTimeout(timeout);
  }, [saveStatus]);

  function updateStepField(stepId: string, field: keyof SequenceStep, value: string | number) {
    const updatedSteps = sequenceData.steps.map(step =>
      step.id === stepId ? { ...step, [field]: value } : step
    );

    setSequenceData({ ...sequenceData, steps: updatedSteps });
  }

  function addStep() {
    const newStepNumber = sequenceData.steps.length + 1;
    const lastStepDay = sequenceData.steps.length > 0
      ? sequenceData.steps[sequenceData.steps.length - 1].day
      : 0;

    const newStep: SequenceStep = {
      id: `step-${Date.now()}`,
      step: newStepNumber,
      day: lastStepDay + 3,
      channel: 'Email',
      message: 'Enter your message here...',
      timing: `Day ${lastStepDay + 3}`
    };

    setSequenceData({
      ...sequenceData,
      steps: [...sequenceData.steps, newStep]
    });
  }

  function removeStep(stepId: string) {
    const updatedSteps = sequenceData.steps
      .filter(step => step.id !== stepId)
      .map((step, idx) => ({ ...step, step: idx + 1 }));

    setSequenceData({
      ...sequenceData,
      steps: updatedSteps
    });
  }

  function validateSequence(): boolean {
    if (!sequenceData.steps || sequenceData.steps.length === 0) {
      setErrorMessage('Sequence must have at least one step');
      return false;
    }

    for (const step of sequenceData.steps) {
      if (!step.message || step.message.trim() === '') {
        setErrorMessage('All steps must have a message');
        return false;
      }
      if (!step.channel) {
        setErrorMessage('All steps must have a channel selected');
        return false;
      }
      if (step.channel === 'Email' && (!step.subject || step.subject.trim() === '')) {
        setErrorMessage('Email steps must have a subject line');
        return false;
      }
    }

    return true;
  }

  async function handleSaveSequence() {
    if (!sessionId || isSaving) return;

    if (!validateSequence()) {
      setSaveStatus('error');
      return;
    }

    setIsSaving(true);
    setErrorMessage(null);

    try {
      const response = await fetch('/api/sequences/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          sequence: sequenceData
        })
      });

      const data: SequenceSaveResponse = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || `Failed to save: ${response.status}`);
      }

      setSaveStatus('success');
    } catch (error) {
      console.error('Error saving sequence:', error);
      setSaveStatus('error');
      setErrorMessage(error instanceof Error ? error.message : 'Failed to save sequence');
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="p-4 h-full flex flex-col overflow-hidden">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-lg font-medium">
            {sequenceData.title || 'Untitled Sequence'}
          </h3>
          <p className="text-sm text-gray-500">
            {sequenceData.steps.length} step{sequenceData.steps.length !== 1 ? 's' : ''}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {saveStatus === 'success' && (
            <span className="text-green-500 flex items-center">
              <CheckCircle className="w-4 h-4 mr-1" /> Saved
            </span>
          )}

          {saveStatus === 'error' && (
            <span className="text-red-500 flex items-center">
              <AlertCircle className="w-4 h-4 mr-1" /> Error
            </span>
          )}

          <Button
            onClick={handleSaveSequence}
            disabled={isSaving}
            variant="primary"
            size="sm"
          >
            {isSaving ? 'Saving...' : 'Save Sequence'}
          </Button>
        </div>
      </div>

      {errorMessage && (
        <div className="bg-red-50 p-3 mb-4 text-red-600 text-sm border border-red-100 rounded">
          {errorMessage}
        </div>
      )}

      <div className="overflow-y-auto flex-1 pr-2 space-y-4">
        {sequenceData.steps.map((step, index) => (
          <div key={step.id} className="p-4 border border-gray-200 rounded-lg shadow-sm">
            <div className="flex justify-between items-start mb-2">
              <div className="flex items-center">
                <span className="font-medium mr-2">Step {index + 1}</span>
                <select
                  value={step.channel}
                  onChange={(e) => updateStepField(step.id, 'channel', e.target.value)}
                  className="rounded-md border border-gray-300 px-2 py-1 text-sm"
                >
                  <option value="Email">Email</option>
                  <option value="LinkedIn">LinkedIn</option>
                  <option value="Phone">Phone</option>
                  <option value="Text">Text</option>
                </select>
              </div>

              <Button
                onClick={() => removeStep(step.id)}
                variant="ghost"
                size="sm"
                className="text-gray-400 hover:text-red-500"
              >
                <Trash className="w-4 h-4" />
              </Button>
            </div>

            {step.channel === 'Email' && (
              <input
                type="text"
                placeholder="Subject line"
                value={step.subject || ''}
                onChange={(e) => updateStepField(step.id, 'subject', e.target.value)}
                className="w-full mb-2 px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
            )}

            <textarea
              value={step.message}
              onChange={(e) => updateStepField(step.id, 'message', e.target.value)}
              className="w-full min-h-[120px] px-3 py-2 border border-gray-300 rounded-md text-sm"
              placeholder={`Enter your ${step.channel} message...`}
            />
          </div>
        ))}

        <Button
          onClick={addStep}
          variant="outline"
          className="w-full py-2 mt-4 border border-dashed border-gray-300"
        >
          <Plus className="w-4 h-4 mr-2" /> Add Step
        </Button>
      </div>
    </div>
  );
} 
