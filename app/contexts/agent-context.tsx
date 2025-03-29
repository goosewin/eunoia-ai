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
  deleteSession: (sessionId: string) => void;
  isRenamingSession: boolean;
  currentSessionName: string;
  generateSessionName: (message: string) => void;
}

const AgentContext = createContext<AgentContextType | undefined>(undefined);

export function AgentProvider({ children }: { children: React.ReactNode }) {
  const [sessionId, setSessionId] = useState<string>('');
  const [user, setUser] = useState<User | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isRenamingSession, setIsRenamingSession] = useState(false);
  const [currentSessionName, setCurrentSessionName] = useState('');
  const [isDeletingSession, setIsDeletingSession] = useState(false);
  const isInitialized = useRef(false);

  useEffect(() => {

    if (isInitialized.current || typeof window === 'undefined') return;
    isInitialized.current = true;

    const storedSessionId = localStorage.getItem('sessionId');

    const storedUser = localStorage.getItem('user');
    let userId = '1';

    if (storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser);
        setUser(parsedUser);
        userId = parsedUser.id || '1';
      } catch (error) {
        console.error('Error parsing stored user data:', error);
      }
    }

    const initializeSession = async () => {
      try {

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

        if (storedSessionId) {
          const sessionExists = sessionsData.some(s => s.id === storedSessionId);

          if (sessionExists) {

            setSessionId(storedSessionId);
            console.log('Using existing session ID:', storedSessionId);

            const currentSession = sessionsData.find(s => s.id === storedSessionId);
            if (currentSession) {
              setCurrentSessionName(currentSession.name);
            }
          } else {
            console.log('Stored session ID not found in sessions, creating new session');
            createNewSessionInternal(userId);
          }
        } else {

          createNewSessionInternal(userId);
        }
      } catch (error) {
        console.error('Error initializing session:', error);

        createNewSessionInternal(userId);
      }
    };

    const createNewSessionInternal = (userId: string) => {

      const newSessionId = uuidv4();
      setSessionId(newSessionId);
      localStorage.setItem('sessionId', newSessionId);
      console.log('Created new session ID:', newSessionId);

      const defaultName = `Session ${new Date().toLocaleString()}`;
      setCurrentSessionName(defaultName);

      const newSession = {
        id: newSessionId,
        name: defaultName,
        created_at: new Date().toISOString()
      };

      setSessions(prev => {
        const updated = [...prev, newSession];
        localStorage.setItem('sessions', JSON.stringify(updated));
        return updated;
      });

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

    const newSession = {
      id: newSessionId,
      name: defaultName,
      created_at: new Date().toISOString()
    };

    setSessions(prev => {
      const updated = [...prev, newSession];
      localStorage.setItem('sessions', JSON.stringify(updated));
      return updated;
    });

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

    console.log('Resetting sequence data for new session:', newSessionId);

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

          setSessionId(newSessionId);

          setCurrentSessionName(`New Chat ${new Date().toLocaleString()}`);

          console.log('New session is ready:', newSessionId);
        })
        .catch((error) => {
          console.error('Error in session setup sequence:', error);

          if (resetAttempts < maxResetAttempts) {
            console.log(`Retrying sequence reset (attempt ${resetAttempts + 1}/${maxResetAttempts})...`);
            setTimeout(attemptSequenceReset, 500);
          } else {
            console.log('Maximum reset attempts reached, proceeding without reset');

            setSessionId(newSessionId);
            setCurrentSessionName(`New Chat ${new Date().toLocaleString()}`);
          }
        });
    };

    attemptSequenceReset();
  };

  const switchSession = (sid: string) => {
    if (typeof window === 'undefined') return;

    setSessionId(sid);
    localStorage.setItem('sessionId', sid);

    const currentSession = sessions.find(s => s.id === sid);
    if (currentSession) {
      setCurrentSessionName(currentSession.name);
    }

    console.log('Switched to session ID:', sid);
  };

  const renameSession = (sid: string, name: string) => {
    if (typeof window === 'undefined' || !name.trim()) return;

    setIsRenamingSession(true);

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

        setSessions(prev => {
          const updated = prev.map(session =>
            session.id === sid ? { ...session, name } : session
          );
          localStorage.setItem('sessions', JSON.stringify(updated));
          return updated;
        });

        if (sid === sessionId) {
          setCurrentSessionName(name);
        }

        setIsRenamingSession(false);
      })
      .catch((error) => {
        console.error('Error renaming session:', error);
        setIsRenamingSession(false);

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

  const generateSessionName = (message: string) => {
    if (!sessionId || !message.trim() || currentSessionName !== `Session ${new Date().toLocaleString()}`) {

      return;
    }

    const truncatedMessage = message.substring(0, 30).trim();
    const newName = truncatedMessage + (truncatedMessage.length >= 30 ? '...' : '');

    if (newName.trim()) {
      renameSession(sessionId, newName);
    }
  };

  const deleteSession = (sid: string) => {
    if (typeof window === 'undefined' || isDeletingSession) return;

    setIsDeletingSession(true);

    fetch(`/api/sessions/${sid}`, {
      method: 'DELETE',
    })
      .then(response => {
        if (!response.ok) {
          throw new Error(`Server returned ${response.status}`);
        }
        return response.json();
      })
      .then(() => {

        setSessions(prev => prev.filter(s => s.id !== sid));

        if (sid === sessionId) {
          const remainingSessions = sessions.filter(s => s.id !== sid);
          if (remainingSessions.length > 0) {

            switchSession(remainingSessions[0].id);
          } else {

            createNewSession();
          }
        }
      })
      .catch(error => {
        console.error('Error deleting session:', error);

        setSessions(prev => prev.filter(s => s.id !== sid));
      })
      .finally(() => {
        setIsDeletingSession(false);
      });
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
        deleteSession,
        isRenamingSession,
        currentSessionName,
        generateSessionName
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
