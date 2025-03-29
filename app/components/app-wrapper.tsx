"use client"

import React, { useEffect, useRef, useState } from "react";
import { Socket, io } from 'socket.io-client';
import { useAgent } from "../contexts/agent-context";
import ChatSidebar from "./chat/chat-sidebar";
import { SequenceData } from "./workspace/sequence-types";
import WorkspaceContainer from "./workspace/workspace-container";

type Message = {
  type: "system" | "user" | "assistant";
  text: string;
  timestamp?: string;
  isGenerating?: boolean;
};

interface ApiMessage {
  id: number;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  created_at: string;
  tool_calls?: Array<{
    id: string;
    function: {
      name: string;
      arguments: string;
    };
  }>;
}

export function AppWrapper() {
  const [userInput, setUserInput] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [sequenceData, setSequenceData] = useState<SequenceData | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isFirstUserMessage, setIsFirstUserMessage] = useState(true);
  const [appTitle, setAppTitle] = useState("");
  const [appSubtitle, setAppSubtitle] = useState("");
  const [inputPlaceholder, setInputPlaceholder] = useState("");

  const { sessionId, generateSessionName } = useAgent();

  const socketRef = useRef<Socket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<string>('disconnected');
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [usingTool, setUsingTool] = useState<string | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectTimer = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!sessionId) return;

    setMessages([]);

    const socketUrl = process.env.NEXT_PUBLIC_SOCKETIO_URL || 'http://localhost:5328';

    if (socketRef.current) {
      socketRef.current.disconnect();
    }

    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }

    socketRef.current = io(socketUrl, {
      reconnection: true,
      reconnectionAttempts: maxReconnectAttempts,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 20000,
      transports: ['websocket', 'polling'],
    });

    const socket = socketRef.current;

    socket.on('connect', () => {
      setConnectionStatus('connected');
      setConnectionError(null);
      reconnectAttempts.current = 0;
      socket.emit('join', { session_id: sessionId });
      fetchSequenceData(sessionId);
      fetchAppConfig();
    });

    socket.on('disconnect', () => {
      setConnectionStatus('disconnected');
    });

    socket.on('connect_error', () => {
      reconnectAttempts.current += 1;
      setConnectionStatus('error');

      if (reconnectAttempts.current >= maxReconnectAttempts) {
        setConnectionError('Unable to connect to server. Please refresh the page.');
      } else {
        setConnectionError(`Connection issue. Attempting to reconnect (${reconnectAttempts.current}/${maxReconnectAttempts})...`);

        reconnectTimer.current = setTimeout(() => {
          if (connectionStatus !== 'connected') {
            socket.connect();
          }
        }, 5000);
      }
    });

    socket.on('chat_message', (data: { role: string, content: string }) => {
      if (data.role === 'assistant') {
        setMessages((prev) => [...prev, { type: "system", text: data.content }]);
        setIsGenerating(false);
      }
    });

    socket.on('tool_call_start', (data: { tool: string }) => {
      setUsingTool(data.tool);
    });

    socket.on('tool_call_end', () => {
      setUsingTool(null);
    });

    socket.on('tool_call_error', (data: { tool: string, error: string }) => {
      setUsingTool(null);
      setIsGenerating(false);
      setMessages((prev) => [
        ...prev,
        { type: "system", text: `Error: ${data.error}` }
      ]);
    });

    socket.on('sequence_update', (data: SequenceData | null) => {
      if (data && Array.isArray(data.steps)) {
        if (validateSequenceStructure(data)) {
          setSequenceData(data);
        }
        setIsGenerating(false);
      } else if (data === null) {
        setSequenceData(null);
        setIsGenerating(false);
      }
    });

    fetchChatHistory(sessionId);

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }

      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
        reconnectTimer.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  useEffect(() => {
    if (sessionId) {
      fetchSequenceData(sessionId);
      setIsFirstUserMessage(true);
    } else {
      setSequenceData(null);
    }
  }, [sessionId]);

  const fetchAppConfig = async () => {
    try {
      const response = await fetch('/api/config');
      if (response.ok) {
        const data = await response.json();
        setAppTitle(data.app_title || "");
        setAppSubtitle(data.app_subtitle || "");
        setInputPlaceholder(data.input_placeholder || "");

        if (data.welcome_message && messages.length === 0) {
          setMessages([{ type: "system", text: data.welcome_message }]);
        }
      }
    } catch (err) {
      console.error('Error fetching app configuration:', err);
    }
  };

  const validateSequenceStructure = (data: unknown): boolean => {
    if (!data || typeof data !== 'object') return false;

    const sequenceData = data as Partial<SequenceData>;
    if (!Array.isArray(sequenceData.steps)) return false;

    for (const step of sequenceData.steps) {
      if (typeof step !== 'object' ||
        typeof step.message !== 'string' ||
        !step.id ||
        !step.channel) {
        return false;
      }
    }

    return true;
  };

  const fetchSequenceData = async (sid: string) => {
    try {
      const response = await fetch(`/api/sequences/session?session_id=${sid}`);

      if (response.ok) {
        const data = await response.json();
        if (data?.data?.sequence_data) {
          setSequenceData(data.data.sequence_data);
        } else {
          setSequenceData(null);
        }
      } else if (response.status === 404) {
        setSequenceData(null);
      } else {
        console.error('Error fetching sequence data:', response.statusText);
        setSequenceData(null);
      }
    } catch (err) {
      console.error('Error fetching sequence data:', err);
      setSequenceData(null);
    }
  };

  const fetchChatHistory = async (sid: string) => {
    try {
      const response = await fetch(`/api/chat/${sid}`);
      if (!response.ok) return;

      const data = await response.json();
      if (data.messages && Array.isArray(data.messages)) {
        const uiMessages = data.messages
          .filter((msg: ApiMessage) => msg.role === 'user' || msg.role === 'assistant')
          .map((msg: ApiMessage) => ({
            type: msg.role === 'user' ? 'user' as const : 'system' as const,
            text: msg.content
          }));

        if (uiMessages.length > 0) {
          setMessages(uiMessages);
        }
      }
    } catch (err) {
      console.error('Error fetching chat history:', err);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!userInput.trim() || isGenerating || connectionStatus === 'error' || !socketRef.current || !sessionId) return;

    const userMessage = userInput.trim();
    setUserInput('');

    if (isFirstUserMessage) {
      generateSessionName(userMessage);
      setIsFirstUserMessage(false);
    }

    setMessages(prev => [...prev, { type: 'user', text: userMessage }]);
    socketRef.current.emit('chat_message', {
      session_id: sessionId,
      message: userMessage
    });

    setIsGenerating(true);
  };

  useEffect(() => {
    const messagesContainer = document.getElementById('chat-messages');
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }, [messages, usingTool]);

  // Listen for welcome message events
  useEffect(() => {
    const handleWelcomeMessage = (event: CustomEvent) => {
      if (event.detail && event.detail.message) {
        // Only set welcome message if no messages exist
        setMessages(prevMessages => {
          if (prevMessages.length === 0) {
            return [{ type: 'system', text: event.detail.message }];
          }
          return prevMessages;
        });
      }
    };

    window.addEventListener('welcome_message', handleWelcomeMessage as EventListener);

    return () => {
      window.removeEventListener('welcome_message', handleWelcomeMessage as EventListener);
    };
  }, []);

  return (
    <div className="w-full">
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/10 z-30"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <ChatSidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <header className="flex justify-between items-center p-4 sm:p-6 bg-white border-b border-solid border-[hsl(var(--color-gray-medium))]">
        <div className="flex items-center">
          <button
            onClick={() => setSidebarOpen(true)}
            className="mr-4 p-2 rounded-md hover:bg-gray-100"
            aria-label="Open sidebar"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="3" y1="12" x2="21" y2="12"></line>
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
          </button>
          <h1 className="text-2xl sm:text-3xl font-bold text-[hsl(224_71%_4%)]">{appTitle}</h1>
        </div>

        <div className="flex items-center">
          <h2 className="text-lg sm:text-xl text-[hsl(var(--color-gray))]">{appSubtitle}</h2>
        </div>
      </header>

      {connectionError && (
        <div className="bg-red-100 text-red-700 px-4 py-2 text-center">
          {connectionError}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 p-4 sm:p-6">
        <div className="bg-white rounded-lg shadow-[0_1px_3px_rgba(0,0,0,0.1)] p-4 sm:p-6">
          <div className="space-y-4 mb-6 max-h-[60vh] overflow-y-auto" id="chat-messages">
            {messages.map((message, index) => (
              <div key={index} className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[80%] ${message.type === "user" ? "chat-bubble chat-bubble-user" : "chat-bubble chat-bubble-system"
                    } ${message.isGenerating ? "chat-bubble-generating" : ""}`}
                >
                  {message.text}
                </div>
              </div>
            ))}

            {usingTool && !messages.some(m => m.isGenerating) && (
              <div className="flex justify-center my-2">
                <div className="bg-[hsl(var(--color-indigo-light))] text-[hsl(239_84%_47%)] rounded-full px-3 py-1 text-sm flex items-center">
                  <svg className="animate-spin h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {usingTool}
                </div>
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="mt-auto">
            <div className="relative">
              <input
                type="text"
                placeholder={inputPlaceholder}
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                className="input pr-20 py-5"
                disabled={isGenerating || !!usingTool || connectionStatus === 'error'}
              />
              <button
                type="submit"
                className="btn btn-sm btn-secondary absolute right-2 top-1/2 -translate-y-1/2"
                disabled={isGenerating || !!usingTool || !userInput.trim() || connectionStatus === 'error'}
              >
                SEND
              </button>
            </div>
          </form>
        </div>

        <div className="flex-1 overflow-hidden bg-white">
          <WorkspaceContainer
            sequenceData={sequenceData}
            setSequenceData={setSequenceData}
            isLoading={usingTool === 'generate_sequence'}
          />
        </div>
      </div>
    </div>
  );
}
