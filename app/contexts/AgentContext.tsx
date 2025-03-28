import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { v4 as uuidv4 } from 'uuid';

interface User {
  id?: string;
  name?: string;
  email?: string;
  company?: string;
  company_details?: string;
}

interface Session {
  id: string;
  name: string;
  created_at: string;
  updated_at?: string;
}

interface AgentContextType {
  sessionId: string;
  user: User | null;
  setUser: (user: User) => void;
  createNewSession: () => void;
  sessions: Session[];
  switchSession: (sessionId: string) => void;
  renameSession: (sessionId: string, name: string) => void;
  isRenamingSession: boolean;
  currentSessionName: string;
}

const AgentContext = createContext<AgentContextType | undefined>(undefined);

export function AgentProvider({ children }: { children: React.ReactNode }) {
  const [sessionId, setSessionId] = useState<string>('');
  const [user, setUser] = useState<User | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isRenamingSession, setIsRenamingSession] = useState(false);
  const [currentSessionName, setCurrentSessionName] = useState('');
  const isInitialized = useRef(false);

  useEffect(() => {
    // Only run once to avoid hydration issues
    if (isInitialized.current || typeof window === 'undefined') return;
    isInitialized.current = true;

    // Check if there's a session ID in localStorage
    const storedSessionId = localStorage.getItem('sessionId');
    // Check if there's user data in localStorage
    const storedUser = localStorage.getItem('user');
    let userId = '1'; // Default user ID

    if (storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser);
        setUser(parsedUser);
        userId = parsedUser.id || '1';
      } catch (error) {
        console.error('Error parsing stored user data:', error);
      }
    }

    // Load sessions from server 
    const initializeSession = async () => {
      try {
        // First try to load sessions from server
        const response = await fetch(`/api/sessions?user_id=${userId}`);
        let sessionsData: Session[] = [];

        if (response.ok) {
          const data = await response.json();
          if (Array.isArray(data)) {
            sessionsData = data;
            setSessions(data);
            localStorage.setItem('sessions', JSON.stringify(data));
          }
        } else {
          // Fall back to localStorage if server fails
          const storedSessions = localStorage.getItem('sessions');
          if (storedSessions) {
            try {
              sessionsData = JSON.parse(storedSessions);
              setSessions(sessionsData);
            } catch (e) {
              console.error('Error parsing stored sessions:', e);
            }
          }
        }

        // Now check if the stored session exists in our list of sessions
        if (storedSessionId) {
          const sessionExists = sessionsData.some(s => s.id === storedSessionId);

          if (sessionExists) {
            // Use existing session
            setSessionId(storedSessionId);
            console.log('Using existing session ID:', storedSessionId);

            // Get current session name
            const currentSession = sessionsData.find(s => s.id === storedSessionId);
            if (currentSession) {
              setCurrentSessionName(currentSession.name);
            }
          } else {
            console.log('Stored session ID not found in sessions, creating new session');
            createNewSessionInternal(userId);
          }
        } else {
          // No stored session ID, create new one
          createNewSessionInternal(userId);
        }
      } catch (error) {
        console.error('Error initializing session:', error);
        // If all else fails, create a new session
        createNewSessionInternal(userId);
      }
    };

    const createNewSessionInternal = (userId: string) => {
      // Generate a new session ID
      const newSessionId = uuidv4();
      setSessionId(newSessionId);
      localStorage.setItem('sessionId', newSessionId);
      console.log('Created new session ID:', newSessionId);

      // Default session name
      const defaultName = `Session ${new Date().toLocaleString()}`;
      setCurrentSessionName(defaultName);

      // Create and save new session
      const newSession = {
        id: newSessionId,
        name: defaultName,
        created_at: new Date().toISOString()
      };

      // Update local state
      setSessions(prev => {
        const updated = [...prev, newSession];
        localStorage.setItem('sessions', JSON.stringify(updated));
        return updated;
      });

      // Create session on server
      fetch('/api/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: newSessionId,
          user_id: userId,
          name: defaultName
        }),
      })
        .then((res) => res.json())
        .then((data) => console.log('New session created on server:', data))
        .catch((error) => {
          console.error('Error creating new session:', error);
        });

      // Also notify WebSocket server about new session
      setTimeout(() => {
        fetch('/api/chat/new', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ session_id: newSessionId }),
        })
          .then((res) => res.json())
          .then((data) => console.log('New chat session created on server:', data))
          .catch((error) => {
            console.error('Error creating new chat session:', error);
          });
      }, 500);
    };

    initializeSession();
  }, []);

  // Update the current session name whenever sessionId changes
  useEffect(() => {
    if (!sessionId || sessions.length === 0) return;

    const currentSession = sessions.find(s => s.id === sessionId);
    if (currentSession) {
      setCurrentSessionName(currentSession.name);
    }
  }, [sessionId, sessions]);

  const createNewSession = () => {
    if (typeof window === 'undefined') return;

    const userId = user?.id || '1';
    const newSessionId = uuidv4();
    const defaultName = `Session ${new Date().toLocaleString()}`;

    setSessionId(newSessionId);
    setCurrentSessionName(defaultName);
    localStorage.setItem('sessionId', newSessionId);
    console.log('Created new session ID:', newSessionId);

    // Create and save new session
    const newSession = {
      id: newSessionId,
      name: defaultName,
      created_at: new Date().toISOString()
    };

    // Update local state
    setSessions(prev => {
      const updated = [...prev, newSession];
      localStorage.setItem('sessions', JSON.stringify(updated));
      return updated;
    });

    // Function to handle sequence reset failures
    const fallbackSequenceReset = () => {
      console.log('Using fallback sequence reset mechanism');
      // Even if the reset endpoint fails, we'll still try to create a new chat session
      // which should trigger WebSocket connection and reset on the next page load
      fetch('/api/chat/new', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session_id: newSessionId }),
      })
        .then((res) => res.json())
        .then((data) => console.log('New chat session created on server:', data))
        .catch((error) => {
          console.error('Error creating new chat session:', error);
        });
    };

    // Create session on server
    fetch('/api/sessions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: newSessionId,
        user_id: userId,
        name: defaultName
      }),
    })
      .then((res) => res.json())
      .then((data) => console.log('New session created on server:', data))
      .catch((error) => {
        console.error('Error creating new session:', error);
      });

    // Clear any existing sequence data
    // This will be picked up by the WorkspaceContainer when the sessionId changes
    // but we need to ensure a clean state on session creation
    // Force broadcast an empty sequence to clear the UI
    console.log('Resetting sequence data for new session:', newSessionId);

    // Add maximum retry logic for sequence reset
    let resetAttempts = 0;
    const maxResetAttempts = 3;

    const attemptSequenceReset = () => {
      resetAttempts++;
      console.log(`Sequence reset attempt ${resetAttempts}/${maxResetAttempts}`);

      fetch('/api/sequences/reset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: newSessionId
        }),
      })
        .then((res) => {
          if (!res.ok) {
            throw new Error(`Server returned ${res.status}: ${res.statusText}`);
          }
          return res.json();
        })
        .then((data) => {
          console.log('Sequence data reset successful:', data);
          // Now create the chat session
          return fetch('/api/chat/new', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ session_id: newSessionId }),
          });
        })
        .then((res) => {
          if (!res.ok) {
            throw new Error(`Chat creation failed: ${res.status}`);
          }
          return res.json();
        })
        .then((data) => {
          console.log('New chat session created on server:', data);
        })
        .catch((error) => {
          console.error('Error in session setup sequence:', error);

          // Retry logic for reset failures
          if (resetAttempts < maxResetAttempts) {
            console.log(`Retrying sequence reset (attempt ${resetAttempts + 1}/${maxResetAttempts})...`);
            setTimeout(attemptSequenceReset, 500); // Retry after short delay
          } else {
            console.log('Maximum reset attempts reached, using fallback');
            fallbackSequenceReset();
          }
        });
    };

    // Start the sequence reset attempt chain
    attemptSequenceReset();
  };

  const switchSession = (sid: string) => {
    if (typeof window === 'undefined') return;

    setSessionId(sid);
    localStorage.setItem('sessionId', sid);

    // Update current session name
    const currentSession = sessions.find(s => s.id === sid);
    if (currentSession) {
      setCurrentSessionName(currentSession.name);
    }

    console.log('Switched to session ID:', sid);
  };

  const renameSession = (sid: string, name: string) => {
    if (typeof window === 'undefined' || !name.trim()) return;

    setIsRenamingSession(true);

    // Update session name via API
    fetch(`/api/sessions/${sid}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name }),
    })
      .then((res) => res.json())
      .then((data) => {
        console.log('Session renamed on server:', data);

        // Update local state after successful server update
        setSessions(prev => {
          const updated = prev.map(session =>
            session.id === sid ? { ...session, name } : session
          );
          localStorage.setItem('sessions', JSON.stringify(updated));
          return updated;
        });

        // Update current session name if this is the active session
        if (sid === sessionId) {
          setCurrentSessionName(name);
        }

        setIsRenamingSession(false);
      })
      .catch((error) => {
        console.error('Error renaming session:', error);
        setIsRenamingSession(false);

        // Still update local state even if server fails
        setSessions(prev => {
          const updated = prev.map(session =>
            session.id === sid ? { ...session, name } : session
          );
          localStorage.setItem('sessions', JSON.stringify(updated));
          return updated;
        });
      });
  };

  const updateUser = (userData: User) => {
    if (typeof window === 'undefined') return;

    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));

    // Save user data to backend
    if (userData.name && userData.email) {
      fetch('/api/user', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      })
        .then((res) => res.json())
        .catch((error) => {
          console.error('Error saving user data:', error);
        });
    }
  };

  return (
    <AgentContext.Provider
      value={{
        sessionId,
        user,
        setUser: updateUser,
        createNewSession,
        sessions,
        switchSession,
        renameSession,
        isRenamingSession,
        currentSessionName
      }}
    >
      {children}
    </AgentContext.Provider>
  );
}

export function useAgent() {
  const context = useContext(AgentContext);
  if (context === undefined) {
    throw new Error('useAgent must be used within an AgentProvider');
  }
  return context;
} 
