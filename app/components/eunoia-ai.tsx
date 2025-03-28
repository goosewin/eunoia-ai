"use client"

import React, { useEffect, useRef, useState } from "react";
import { Socket, io } from 'socket.io-client';
import { useAgent } from "../contexts/AgentContext";
import WorkspaceContainer from "./Workspace/WorkspaceContainer";

type Message = {
  type: "system" | "user" | "assistant";
  text: string;
  timestamp?: string;
};

interface SequenceData {
  id?: string;
  title: string;
  target_role: string;
  industry: string;
  company: string;
  steps: Array<{
    id: string;
    step: number;
    day: number;
    channel: string;
    subject?: string;
    message: string;
    timing: string;
  }>;
}

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

export function EunoiaAI() {
  // State for the chat and sequence
  const [userInput, setUserInput] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    { type: "system", text: "Hi! I'm Eunoia, your AI recruiting assistant. What kind of recruiting campaign are you looking to run today?" }
  ])
  const [showSessionPicker, setShowSessionPicker] = useState(false)
  const [isEditingSessionName, setIsEditingSessionName] = useState(false)
  const [newSessionName, setNewSessionName] = useState("")
  const [hasRenamed, setHasRenamed] = useState(false)

  // Get session data from context
  const {
    sessionId,
    sessions,
    switchSession,
    createNewSession,
    renameSession,
    currentSessionName,
    isRenamingSession
  } = useAgent();

  // Socket and session management
  const socketRef = useRef<Socket | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<string>('disconnected')
  const [connectionError, setConnectionError] = useState<string | null>(null)
  const [usingTool, setUsingTool] = useState<string | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5
  const reconnectTimer = useRef<NodeJS.Timeout | null>(null)

  // Initialize websocket connection and session
  useEffect(() => {
    if (!sessionId) return;

    // Reset messages for new session
    setMessages([
      { type: "system", text: "Hi! I'm Eunoia, your AI recruiting assistant. What kind of recruiting campaign are you looking to run today?" }
    ]);

    // Connect to websocket
    const socketUrl = process.env.NEXT_PUBLIC_SOCKETIO_URL || 'http://localhost:5328';
    console.log('Connecting to socket at:', socketUrl);

    // Clean up previous connection if it exists
    if (socketRef.current) {
      console.log('Cleaning up previous socket connection');
      socketRef.current.disconnect();
    }

    // Clear any existing reconnect timer
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
    })

    const socket = socketRef.current

    // Setup socket event listeners
    socket.on('connect', () => {
      console.log('Connected to server with ID:', socket.id)
      setConnectionStatus('connected')
      setConnectionError(null)
      reconnectAttempts.current = 0

      // Join room based on session ID
      socket.emit('join', { session_id: sessionId })
      console.log('Joining session room:', sessionId)
    })

    socket.on('disconnect', () => {
      console.log('Disconnected from server')
      setConnectionStatus('disconnected')
    })

    socket.on('connect_error', (err) => {
      console.error('Connection error:', err)
      reconnectAttempts.current += 1
      setConnectionStatus('error')

      if (reconnectAttempts.current >= maxReconnectAttempts) {
        setConnectionError('Unable to connect to server. Please refresh the page.')
      } else {
        setConnectionError(`Connection issue. Attempting to reconnect (${reconnectAttempts.current}/${maxReconnectAttempts})...`)

        // Manual reconnection attempt if socket.io reconnection fails
        reconnectTimer.current = setTimeout(() => {
          if (connectionStatus !== 'connected') {
            console.log(`Manual reconnection attempt ${reconnectAttempts.current}`)
            socket.connect()
          }
        }, 5000)
      }
    })

    socket.on('chat_message', (data: { role: string, content: string }) => {
      console.log('Received chat message:', data)
      if (data.role === 'assistant') {
        setMessages((prev) => [
          ...prev,
          { type: "system", text: data.content }
        ])
        setIsGenerating(false)
      }
    })

    socket.on('tool_call_start', (data: { tool: string }) => {
      console.log('Tool call started:', data.tool)
      setUsingTool(data.tool)

      if (data.tool === 'generate_sequence') {
        setMessages((prev) => [
          ...prev,
          { type: "system", text: "Generating sequence...", isGenerating: true }
        ])
      }
    })

    socket.on('tool_call_end', () => {
      console.log('Tool call ended')
      setUsingTool(null)
    })

    socket.on('tool_call_error', (data: { tool: string, error: string }) => {
      console.error(`Error with tool ${data.tool}:`, data.error)
      setUsingTool(null)
      setIsGenerating(false)

      // Show error message to user
      setMessages((prev) => [
        ...prev,
        {
          type: "system",
          text: `Sorry, I encountered an error while generating content: ${data.error}`
        }
      ])
    })

    socket.on('sequence_update', (data: SequenceData) => {
      console.log('Main component received sequence update:', data)
      console.log('Sequence has', data.steps?.length || 0, 'steps')

      // Remove any "Generating sequence..." messages and don't add the sequence to chat
      setMessages((prev) => {
        const filteredMessages = prev.filter(msg => !msg.isGenerating)
        return filteredMessages
      })

      // Stop the generating indicator
      setIsGenerating(false)
    })

    // Fetch chat history when component mounts
    fetchChatHistory(sessionId)

    // Cleanup on unmount
    return () => {
      console.log('Cleaning up socket connection')
      if (socketRef.current) {
        socketRef.current.disconnect()
      }

      // Clear any reconnect timer
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current)
        reconnectTimer.current = null
      }
    }
  }, [sessionId])

  // Function to fetch chat history
  const fetchChatHistory = async (sid: string) => {
    try {
      const response = await fetch(`/api/chat/${sid}`)
      if (!response.ok) return

      const data = await response.json()

      if (data.messages && Array.isArray(data.messages)) {
        // Convert messages from API format to our UI format
        const uiMessages = data.messages
          .filter((msg: ApiMessage) => msg.role === 'user' || msg.role === 'assistant')
          .map((msg: ApiMessage) => ({
            type: msg.role === 'user' ? 'user' as const : 'system' as const,
            text: msg.content
          }))

        if (uiMessages.length > 0) {
          setMessages(uiMessages)
        }
      }
    } catch (error) {
      console.error('Error fetching chat history:', error)
    }
  }

  // Submit handler for the chat form
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!userInput.trim() || isGenerating || !sessionId) return

    // Add user message to UI
    setMessages((prev) => [...prev, { type: "user", text: userInput }])
    setIsGenerating(true)

    // Try socket first if connected
    if (socketRef.current && socketRef.current.connected) {
      console.log('Sending message via socket:', userInput)
      socketRef.current.emit('chat_message', {
        session_id: sessionId,
        message: userInput,
        user_id: 1,
      })
    } else {
      console.log('Socket not connected, using HTTP fallback')
      try {
        // Send message to backend using HTTP
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            session_id: sessionId,
            message: userInput,
          }),
        })

        if (!response.ok) {
          throw new Error(`Server error: ${response.status}`)
        }
      } catch (error) {
        console.error('Error sending message:', error)
        setIsGenerating(false)
        setMessages((prev) => [
          ...prev,
          { type: "system", text: "Sorry, there was an error processing your request. Please try again." }
        ])
      }
    }

    // Clear input field
    setUserInput("")
  }

  // Handle session switching
  const handleSessionSwitch = (sid: string) => {
    switchSession(sid);
    setShowSessionPicker(false);
  }

  // Auto-scroll messages
  useEffect(() => {
    const messagesContainer = document.getElementById('chat-messages');
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }, [messages, usingTool]);

  // Start editing session name
  const handleStartRenaming = () => {
    setNewSessionName(currentSessionName);
    setIsEditingSessionName(true);
  }

  // Save new session name
  const handleSaveSessionName = () => {
    if (newSessionName.trim() && newSessionName !== currentSessionName) {
      renameSession(sessionId, newSessionName.trim());
    }
    setIsEditingSessionName(false);
    setHasRenamed(true);
  }

  // Cancel editing session name
  const handleCancelRenaming = () => {
    setIsEditingSessionName(false);
  }

  return (
    <div className="w-full">
      {/* Header */}
      <header className="flex flex-col sm:flex-row justify-between items-center p-4 sm:p-6 bg-white border-b border-solid border-[hsl(var(--color-gray-medium))]">
        <h1 className="text-2xl sm:text-3xl font-bold text-[hsl(224_71%_4%)] mb-2 sm:mb-0">EUNOIA AI</h1>

        <div className="flex items-center">
          {/* Session Picker */}
          <div className="relative mr-4">
            {isEditingSessionName ? (
              <div className="flex items-center">
                <input
                  type="text"
                  value={newSessionName}
                  onChange={(e) => setNewSessionName(e.target.value)}
                  className="mr-2 w-48"
                  placeholder="Session name..."
                  disabled={isRenamingSession}
                />
                <div className="flex space-x-1">
                  <button
                    size="sm"
                    variant="outline"
                    onClick={handleSaveSessionName}
                    disabled={isRenamingSession}
                  >
                    Save
                  </button>
                  <button
                    size="sm"
                    variant="outline"
                    onClick={handleCancelRenaming}
                    disabled={isRenamingSession}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center">
                <button
                  onClick={() => setShowSessionPicker(!showSessionPicker)}
                  className="px-3 py-1 bg-gray-100 rounded-md flex items-center mr-2"
                >
                  <span className="mr-2">{currentSessionName}</span>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="6 9 12 15 18 9"></polyline>
                  </svg>
                </button>

                <button
                  onClick={handleStartRenaming}
                  className="text-gray-500 hover:text-gray-700"
                  title="Rename session"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 20h9"></path>
                    <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
                  </svg>
                </button>
              </div>
            )}

            {showSessionPicker && (
              <div className="absolute top-full mt-1 right-0 bg-white shadow-lg rounded-md p-2 z-10 w-64">
                <div className="max-h-60 overflow-y-auto">
                  {sessions.map(session => (
                    <button
                      key={session.id}
                      onClick={() => handleSessionSwitch(session.id)}
                      className={`w-full text-left px-3 py-2 rounded-md hover:bg-gray-100 ${session.id === sessionId ? 'bg-blue-50 text-blue-600' : ''
                        }`}
                    >
                      {session.name}
                    </button>
                  ))}
                </div>
                <button
                  onClick={() => { createNewSession(); setShowSessionPicker(false); }}
                  className="w-full mt-2 px-3 py-2 bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100"
                >
                  + New Session
                </button>
              </div>
            )}
          </div>

          <h2 className="text-lg sm:text-xl text-[hsl(var(--color-gray))]">AI Recruiting Assistant</h2>
        </div>
      </header>

      {/* Connection status indicator (only show when there's an error) */}
      {connectionError && (
        <div className="bg-red-100 text-red-700 px-4 py-2 text-center">
          {connectionError}
        </div>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 p-4 sm:p-6">
        {/* Chat Panel */}
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

            {/* Tool usage indicator */}
            {usingTool && !messages.some(m => m.isGenerating) && (
              <div className="flex justify-center my-2">
                <div className="bg-[hsl(var(--color-indigo-light))] text-[hsl(239_84%_47%)] rounded-full px-3 py-1 text-sm flex items-center">
                  <svg className="animate-spin h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Using tool: {usingTool}
                </div>
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="mt-auto">
            <div className="relative">
              <input
                type="text"
                placeholder="Type your message..."
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

        {/* Sequence Workspace Panel */}
        <div className="bg-white rounded-lg shadow-[0_1px_3px_rgba(0,0,0,0.1)] h-[calc(100vh-200px)] overflow-hidden">
          <WorkspaceContainer sessionId={sessionId} userId="1" />
        </div>
      </div>
    </div>
  )
} 
