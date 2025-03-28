import { useEffect, useRef, useState } from 'react';
import { Socket, io } from 'socket.io-client';
import { useAgent } from '../../contexts/AgentContext';
import SequenceEditor from './SequenceEditor';
import { SequenceData, SequenceStep } from './sequenceTypes';

interface WorkspaceContainerProps {
  sessionId: string;
  userId?: string;
}

export default function WorkspaceContainer({ sessionId, userId }: WorkspaceContainerProps) {
  const [sequenceData, setSequenceData] = useState<SequenceData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<Socket | null>(null);
  const { currentSessionName } = useAgent();
  const socketInitialized = useRef(false);
  const loadingAttempts = useRef(0);
  const isFirstLoad = useRef(true);

  // Establish socket connection
  useEffect(() => {
    // Only run this once at the start
    if (!sessionId) return;

    console.log('Starting WorkspaceContainer setup for session:', sessionId);

    // Cleanup state when session changes
    setSequenceData(null);
    setError(null);
    setIsLoading(true);

    // Prevent multiple socket connections
    if (socketRef.current?.connected) {
      console.log('Disconnecting existing socket before creating new one');
      socketRef.current.disconnect();
    }

    // Initialize socket with better reconnection settings
    const socket = io({
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      timeout: 10000,
      path: '/socket.io',
      transports: ['websocket', 'polling'], // Try websocket first, fall back to polling
      query: { session_id: sessionId } // Pass session ID as a query parameter for easier identification
    });

    socketRef.current = socket;
    socketInitialized.current = false;
    loadingAttempts.current = 0;
    isFirstLoad.current = true;

    // Immediately attempt to load sequence data - don't wait for socket connection
    if (sessionId) {
      console.log('Initial sequence data fetch for session:', sessionId);
      loadSequenceData();
    }

    // Set up socket event listeners
    socket.on('connect', () => {
      console.log('Workspace socket connected, joining room:', sessionId);
      socket.emit('join', { session_id: sessionId });
      socketInitialized.current = true;
    });

    socket.on('connect_error', (err) => {
      console.error('Socket connection error:', err);
      // Still try to load sequences even if socket fails
      if (!socketInitialized.current && loadingAttempts.current < 2) {
        loadingAttempts.current++;
        console.log(`Socket connection failed, trying direct load (attempt ${loadingAttempts.current})`);
        loadSequenceData();
      }
    });

    socket.on('room_joined', (data) => {
      console.log('Joined room successfully:', data);
      // Load sequence data after we've successfully joined the room
      if (isFirstLoad.current) {
        console.log('First room join, loading sequences');
        loadSequenceData();
        isFirstLoad.current = false;
      }
    });

    socket.on('sequence_update', (data) => {
      console.log('Received sequence update via socket:', data);
      setSequenceData(data);
      setIsLoading(false);
      setError(null);
    });

    socket.on('error', (err) => {
      console.error('Socket error:', err);
      setError('Socket error: ' + (err.message || 'Unknown error'));
    });

    // Clean up on unmount or session change
    return () => {
      console.log('Cleaning up socket connection for session:', sessionId);
      socket.disconnect();
      socketRef.current = null;
      socketInitialized.current = false;
      loadingAttempts.current = 0;
      isFirstLoad.current = true;
    };
  }, [sessionId]);

  // Load sequence data function - separated for reuse
  const loadSequenceData = async () => {
    if (!sessionId) return;

    try {
      console.log('Loading sequences for session:', sessionId);
      setIsLoading(true);

      // Try to load associated sequence for this session
      const response = await fetch(`/api/sequences?session_id=${sessionId}`);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error loading sequences:', errorText);
        setError('Failed to load sequences');
        setIsLoading(false);
        return;
      }

      const data = await response.json();
      console.log('Found sequences for session:', data?.length || 0);

      // If we found sequences for this session
      if (Array.isArray(data) && data.length > 0) {
        // Get the most recent sequence
        const mostRecentSequence = data[0];
        console.log('Using most recent sequence:', mostRecentSequence.id);

        // Now fetch the full sequence data
        const seqResponse = await fetch(`/api/sequences/${mostRecentSequence.id}`);

        if (seqResponse.ok) {
          const sequenceDetails = await seqResponse.json();
          if (sequenceDetails.sequence_data) {
            console.log('Loaded sequence data successfully', sequenceDetails.sequence_data);
            setSequenceData(sequenceDetails.sequence_data);
            setError(null);
          } else {
            console.log('No sequence data found in sequence, will use default');
            setSequenceData(createDefaultSequence());
          }
        } else {
          const errorText = await seqResponse.text();
          console.error('Error loading sequence details:', errorText);
          setError('Failed to load sequence details');
        }
      } else {
        console.log('No sequences found for this session, using default empty state');
        // No error here - it's normal for a new session to have no sequences
        setSequenceData(null);
        setError(null);
      }
    } catch (error) {
      console.error('Error loading sequence data:', error);
      setError('Failed to load sequence data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Create default sequence data if none exists
  const createDefaultSequence = (): SequenceData => {
    return {
      id: `sequence_${Date.now()}`,
      title: `Recruiting Sequence for ${currentSessionName || 'New Campaign'}`,
      target_role: 'Software Engineer',
      industry: 'Technology',
      steps: [
        {
          id: 'step_1',
          step: 1,
          day: 0,
          channel: 'Email',
          subject: 'Exciting opportunity at our company',
          message: 'Hello,\n\nI hope this message finds you well. I came across your profile and was impressed by your experience. We have an opening that might interest you.\n\nWould you be interested in learning more?\n\nBest regards,\n[Your Name]',
          timing: 'Day 0'
        }
      ]
    };
  };

  const handleSaveSequence = async (sequence: SequenceData) => {
    try {
      setIsLoading(true);
      console.log('Saving sequence:', sequence);

      // Send the updated sequence to the server
      const response = await fetch('/api/sequences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId || '1',
          session_id: sessionId,
          title: sequence.title,
          target_role: sequence.target_role,
          target_industry: sequence.industry,
          sequence_data: sequence,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save sequence');
      }

      const savedSequence = await response.json();
      console.log('Sequence saved successfully:', savedSequence);

      // Update the sequence data with the saved ID if needed
      if (savedSequence && savedSequence.id) {
        const updatedSequence = {
          ...sequence,
          id: savedSequence.id
        };
        setSequenceData(updatedSequence);
      }

      // Also emit the changes via socket
      if (socketRef.current?.connected) {
        console.log('Emitting sequence_edit via socket');
        socketRef.current?.emit('sequence_edit', {
          session_id: sessionId,
          sequence_id: sequence.id || 'new',
          changes: sequence,
        });
      } else {
        console.warn('Socket not connected when trying to emit sequence_edit');
      }

      setError(null);
    } catch (error) {
      console.error('Error saving sequence:', error);
      setError('Failed to save sequence changes');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddStep = (sequenceData: SequenceData) => {
    // Generate a unique ID for the new step
    const newId = `step_${Date.now()}`;
    const newStepNumber = sequenceData.steps.length + 1;

    // Default day calculation: use the last step's day + 3, or start at day 0
    const lastStep = sequenceData.steps[sequenceData.steps.length - 1];
    const newDay = lastStep ? lastStep.day + 3 : 0;

    // Create a new step with default values
    const newStep: SequenceStep = {
      id: newId,
      step: newStepNumber,
      day: newDay,
      channel: 'Email',
      subject: `Follow-up message ${newStepNumber}`,
      message: 'Enter your message here...',
      timing: `Day ${newDay}`
    };

    // Add to sequence data
    const updatedSequence = {
      ...sequenceData,
      steps: [...sequenceData.steps, newStep]
    };

    return updatedSequence;
  };

  // Create default sequence data or handle empty state
  const getSequenceData = () => {
    // If we're loading, return undefined
    if (isLoading) return undefined;

    // If we have sequence data, use it
    if (sequenceData) return sequenceData;

    // If there's an error, return undefined to let SequenceEditor handle it
    if (error) return undefined;

    // Otherwise create a default sequence
    return createDefaultSequence();
  };

  // Retry loading on error
  const handleRetry = () => {
    setError(null);
    loadSequenceData();

    // Also try reconnecting socket if needed
    if (!socketRef.current?.connected) {
      console.log('Reconnecting socket on retry');
      socketRef.current?.connect();
    }
  };

  return (
    <div className="h-full flex flex-col overflow-auto">
      {isLoading && (
        <div className="p-4 bg-blue-50 text-blue-600 text-center">
          <span className="animate-pulse">Loading sequence data...</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 text-red-600 text-center">
          <p>{error}</p>
          <button
            onClick={handleRetry}
            className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200"
          >
            Retry
          </button>
        </div>
      )}

      {!isLoading && !sequenceData && !error && (
        <div className="p-4 bg-gray-50 text-gray-600 text-center">
          <p>No sequence data yet. Start a conversation to generate a sequence or create one manually.</p>
        </div>
      )}

      <SequenceEditor
        sequenceData={getSequenceData()}
        socket={socketRef.current}
        onSave={handleSaveSequence}
        onAddStep={handleAddStep}
      />
    </div>
  );
} 
