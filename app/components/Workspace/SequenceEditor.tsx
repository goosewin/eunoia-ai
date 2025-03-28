import { useAgent } from '@/app/contexts/AgentContext';
import { useEffect, useState } from 'react';
import { Socket } from 'socket.io-client';
import { Button } from '../UI/Button';
import SequenceStep from './SequenceStep';
import { SequenceData } from './sequenceTypes';

interface SequenceEditorProps {
  sequenceData?: SequenceData | null;
  socket?: Socket | null;
  onSave?: (sequence: SequenceData) => void;
  onAddStep?: (sequenceData: SequenceData) => SequenceData;
}

export default function SequenceEditor({
  sequenceData,
  socket,
  onSave,
  onAddStep,
}: SequenceEditorProps) {
  const { sessionId } = useAgent();
  const [sequence, setSequence] = useState<SequenceData>({
    title: '',
    target_role: '',
    industry: '',
    company: '',
    steps: [],
  });
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (!sequenceData) {
      // Reset to empty sequence when sequenceData is null
      setSequence({
        title: '',
        target_role: '',
        industry: '',
        company: '',
        steps: [],
      });
      return;
    }

    console.log('SequenceEditor received new sequenceData prop:', sequenceData);
    console.log('Sequence has', sequenceData.steps?.length || 0, 'steps');

    // Always ensure steps array is valid
    const validSteps = Array.isArray(sequenceData.steps) ? sequenceData.steps : [];

    // Apply the new sequence data
    setSequence({
      ...sequenceData,
      steps: validSteps.map((step, index) => ({
        ...step,
        id: step.id || `step_${index + 1}`,
        step: step.step || index + 1,
        day: step.day || index * 3,
        channel: step.channel || 'Email',
        timing: step.timing || `Day ${index * 3}`
      }))
    });

    console.log('Sequence steps after processing:', validSteps.length);
  }, [sequenceData]);

  useEffect(() => {
    if (!socket) return;

    // Listen for sequence updates from the agent
    const handleSequenceUpdate = (data: SequenceData) => {
      console.log('SequenceEditor socket event - received sequence update:', data);
      if (data && data.steps && Array.isArray(data.steps)) {
        console.log('Setting sequence from socket with', data.steps.length, 'steps');
        setSequence(data);
      } else {
        console.error('Received invalid sequence data structure:', data);
      }
    };

    // Listen for edit confirmations
    const handleEditConfirmation = (data: { status: string }) => {
      if (data.status === 'received') {
        setSaveSuccess(true);
        setIsSaving(false);

        // Clear success message after 3 seconds
        setTimeout(() => {
          setSaveSuccess(false);
        }, 3000);
      }
    };

    socket.on('sequence_update', handleSequenceUpdate);
    socket.on('edit_received', handleEditConfirmation);

    return () => {
      socket.off('sequence_update', handleSequenceUpdate);
      socket.off('edit_received', handleEditConfirmation);
    };
  }, [socket]);

  const handleMetadataChange = (field: string, value: string) => {
    setSequence((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleStepEdit = (stepIndex: number, field: string, value: string) => {
    const updatedSteps = [...sequence.steps];
    updatedSteps[stepIndex] = {
      ...updatedSteps[stepIndex],
      [field]: value,
    };

    setSequence((prev) => ({
      ...prev,
      steps: updatedSteps,
    }));
  };

  const handleAddStep = () => {
    if (onAddStep && sequence) {
      // Use the parent component's add step function if available
      const updatedSequence = onAddStep(sequence);
      setSequence(updatedSequence);
    } else {
      // Default implementation
      const nextStep = sequence.steps.length + 1;
      const lastStep = sequence.steps[sequence.steps.length - 1];
      const newDay = lastStep ? lastStep.day + 3 : 0;

      const newStep = {
        id: `step_${Date.now()}`,
        step: nextStep,
        day: newDay,
        channel: 'Email',
        subject: 'Follow up',
        message: 'Enter your message here...',
        timing: `Day ${newDay}`,
      };

      setSequence((prev) => ({
        ...prev,
        steps: [...prev.steps, newStep],
      }));
    }
  };

  const handleRemoveStep = (stepIndex: number) => {
    const updatedSteps = sequence.steps.filter((_, index) => index !== stepIndex);

    // Recalculate step numbers
    const renumberedSteps = updatedSteps.map((step, idx) => ({
      ...step,
      step: idx + 1
    }));

    setSequence((prev) => ({
      ...prev,
      steps: renumberedSteps,
    }));
  };

  const handleSaveSequence = () => {
    setIsSaving(true);
    setSaveSuccess(false);

    if (onSave) {
      onSave(sequence);
    }

    // Emit via socket if available
    if (socket) {
      socket.emit('sequence_edit', {
        session_id: sessionId,
        sequence_id: sequence.id,
        changes: sequence,
      });
    }

    // Also save to API if needed
    fetch('/api/sequences', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        title: sequence.title,
        target_role: sequence.target_role,
        target_industry: sequence.industry,
        sequence_data: sequence,
        user_id: '1', // Default user ID if not available
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        console.log('Sequence saved:', data);
        setIsSaving(false);
        setSaveSuccess(true);

        // Clear success message after 3 seconds
        setTimeout(() => {
          setSaveSuccess(false);
        }, 3000);
      })
      .catch((error) => {
        console.error('Error saving sequence:', error);
        setIsSaving(false);
      });
  };

  if (!sequence || !sequenceData) {
    return (
      <div className="p-6 text-center">
        <p className="text-gray-500">No sequence data available yet.</p>
        <p className="text-gray-500 text-sm">
          Start a conversation to generate a recruitment sequence.
        </p>
      </div>
    );
  }

  return (
    <div className="p-4">
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">Sequence Details</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Title
            </label>
            <input
              type="text"
              value={sequence.title}
              onChange={(e) => handleMetadataChange('title', e.target.value)}
              className="w-full border rounded-md p-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Target Role
            </label>
            <input
              type="text"
              value={sequence.target_role}
              onChange={(e) => handleMetadataChange('target_role', e.target.value)}
              className="w-full border rounded-md p-2"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Industry
            </label>
            <input
              type="text"
              value={sequence.industry}
              onChange={(e) => handleMetadataChange('industry', e.target.value)}
              className="w-full border rounded-md p-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Company
            </label>
            <input
              type="text"
              value={sequence.company || ''}
              onChange={(e) => handleMetadataChange('company', e.target.value)}
              className="w-full border rounded-md p-2"
            />
          </div>
        </div>
      </div>

      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Steps</h2>
          <Button onClick={handleAddStep} variant="secondary">
            Add Step
          </Button>
        </div>

        {sequence.steps.map((step, index) => (
          <SequenceStep
            key={step.id || index}
            step={step.step || index + 1}
            channel={step.channel}
            timing={step.timing || `Day ${step.day}`}
            subject={step.subject}
            message={step.message}
            onEdit={(_, field, value) => handleStepEdit(index, field, value)}
            onRemove={() => handleRemoveStep(index)}
          />
        ))}

        {sequence.steps.length === 0 && (
          <p className="text-gray-500 text-center my-8">
            No steps in this sequence yet. Add your first step or let the AI generate one for you.
          </p>
        )}
      </div>

      <div className="mt-6 flex items-center justify-end space-x-3">
        {isSaving && (
          <div className="flex items-center text-blue-600">
            <svg className="animate-spin h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Saving...
          </div>
        )}

        {saveSuccess && (
          <div className="text-green-600 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Saved
          </div>
        )}

        <Button onClick={handleSaveSequence} disabled={isSaving}>
          {isSaving ? 'Saving...' : 'Save Sequence'}
        </Button>
      </div>
    </div>
  );
} 
