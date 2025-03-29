import { useAgent } from '@/app/contexts/agent-context';
import { useEffect, useRef, useState } from 'react';
import { Socket, io } from 'socket.io-client';
import { Button } from '../ui/button';
import SequenceEditor from './sequence-editor';
import { SequenceData, SequenceResponse } from './sequence-types';

interface WorkspaceContainerProps {
  sequenceData: SequenceData | null;
  setSequenceData: (data: SequenceData | null) => void;
  isLoading: boolean;
}

export default function WorkspaceContainer({
  sequenceData,
  setSequenceData,
}: WorkspaceContainerProps) {
  const [error, setError] = useState<string | null>(null);
  const { sessionId } = useAgent();
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    const socketUrl = process.env.NEXT_PUBLIC_SOCKETIO_URL || 'http://localhost:5328';

    if (socketRef.current) {
      socketRef.current.disconnect();
    }

    socketRef.current = io(socketUrl, {
      transports: ['websocket', 'polling'],
    });

    socketRef.current.on('connect', () => {
      socketRef.current?.emit('join', { session_id: sessionId });
      setError(null);
    });

    socketRef.current.on('connect_error', () => {
      setError('Failed to connect to server. Please try again.');
    });

    socketRef.current.on('sequence_update', (data: SequenceData | null) => {
      if (data && Array.isArray(data.steps)) {
        setSequenceData(sanitizeSequenceData(data));
      } else if (data === null) {
        setSequenceData(null);
      }
    });

    fetchSequenceData(sessionId);

    return () => {
      socketRef.current?.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, setSequenceData]);

  async function fetchSequenceData(sessionId: string) {
    try {
      setError(null);
      const response = await fetch(`/api/sequences/session?session_id=${sessionId}`);
      const responseData: SequenceResponse = await response.json();

      if (responseData.success) {
        if (responseData.data?.sequence_data) {
          setSequenceData(sanitizeSequenceData(responseData.data.sequence_data));
        } else {
          setSequenceData(null);
        }
      } else {
        setError(responseData.error || 'Failed to fetch sequence data');
        setSequenceData(null);
      }
    } catch (err) {
      console.error('Error fetching sequence data:', err);
      setError('Network error fetching sequence data');
      setSequenceData(null);
    }
  }

  function sanitizeSequenceData(data: SequenceData): SequenceData {
    if (!data.steps || !Array.isArray(data.steps)) {
      return { ...data, steps: [] };
    }

    const validSteps = data.steps.filter(step =>
      step &&
      typeof step === 'object' &&
      step.message &&
      typeof step.message === 'string' &&
      step.channel &&
      typeof step.channel === 'string'
    );

    return {
      ...data,
      steps: validSteps.map((step, index) => ({
        ...step,
        id: step.id || `step-${index}`
      }))
    };
  }

  function resetSequence() {
    if (!sessionId) return;

    fetch('/api/sequences/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId })
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          setSequenceData(null);
        } else {
          setError(data.error || 'Failed to reset sequence');
        }
      })
      .catch(err => {
        console.error('Error resetting sequence:', err);
        setError('Network error resetting sequence');
      });
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-white">
        <h2 className="text-lg font-semibold">Sequence Builder</h2>
        <div className="flex gap-2">
          {sequenceData && (
            <Button
              onClick={resetSequence}
              variant="outline"
              size="sm"
            >
              Reset Sequence
            </Button>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 p-3 text-red-600 text-sm border-b border-red-100">
          {error}
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        {sequenceData ? (
          <SequenceEditor
            sequenceData={sequenceData}
            setSequenceData={setSequenceData}
            sessionId={sessionId}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center p-6 max-w-sm">
              <h3 className="text-lg font-medium mb-2">No Sequence Available</h3>
              <p className="text-sm text-gray-500 mb-4">
                Chat with the AI assistant to generate a hiring outreach sequence. Simply ask for a sequence for your target role.
              </p>
              <p className="text-xs text-gray-400 mt-2">
                Example: &quot;Create a sequence for Software Engineers&quot; or &quot;I need outreach for Data Scientists&quot;
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
