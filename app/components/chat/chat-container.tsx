import { useEffect, useRef, useState } from 'react';
import { Socket, io } from 'socket.io-client';
import { useAgent } from "../../contexts/agent-context";
import ChatInput from './chat-input';
import ChatMessage from './chat-message';
import ToolCallNotification from './tool-call-notification';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
  isStreaming?: boolean;
  tool_calls?: Record<string, unknown>;
  created_at?: string;
}

interface ChatContainerProps {
  sessionId: string;
  userId?: string | number;
}

export default function ChatContainer({ sessionId, userId }: ChatContainerProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTool, setActiveTool] = useState<string | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [isFirstUserMessage, setIsFirstUserMessage] = useState(true);

  const socketRef = useRef<Socket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { generateSessionName } = useAgent();

  useEffect(() => {

    const socketUrl = process.env.NEXT_PUBLIC_SOCKETIO_URL || (process.env.NODE_ENV === 'production' ? window.location.origin : 'http://localhost:5328');

    console.log('Connecting to socket URL:', socketUrl);

    const newSocket = io(socketUrl, {
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 20000,
    });

    socketRef.current = newSocket;

    newSocket.on('connect', () => {
      console.log('Connected to WebSocket with ID:', newSocket.id);

      newSocket.emit('join', { session_id: sessionId });
      console.log('Joining session room:', sessionId);

      setConnectionError(null);
    });

    newSocket.on('connect_error', (err) => {
      console.error('Connection error:', err);
      setConnectionError(err.message || 'An error occurred with the connection');
    });

    newSocket.on('error', (data) => {
      console.error('Socket error:', data);
      setConnectionError(data.message || 'An error occurred with the connection');
    });

    newSocket.on('message_received', (data) => {
      console.log('Message received by server:', data);

      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: '', isStreaming: true }
      ]);
      setIsLoading(true);
    });

    newSocket.on('room_joined', (data) => {
      console.log('Joined room:', data);
    });

    newSocket.on('chat_message', (data: { role: string, content: string }) => {
      console.log('Received message from server:', data);

      setMessages(prev => prev.filter(msg => !msg.isStreaming));

      setMessages(prev => [
        ...prev,
        {
          role: data.role as 'user' | 'assistant' | 'system',
          content: data.content,
          timestamp: new Date().toISOString()
        }
      ]);

      setIsLoading(false);
    });

    newSocket.on('tool_call_start', (data: { tool: string }) => {
      console.log('Tool call started:', data.tool);
      setActiveTool(data.tool);

      setMessages(prev => prev.filter(msg => !msg.isStreaming));
    });

    newSocket.on('tool_call_end', () => {
      console.log('Tool call ended');
      setActiveTool(null);
    });

    newSocket.on('processing_complete', () => {
      console.log('Processing complete');
      setIsLoading(false);

      setMessages(prev => prev.filter(msg => !msg.isStreaming));
    });

    return () => {
      console.log('Disconnecting socket');
      newSocket.disconnect();
    };
  }, [sessionId]);

  useEffect(() => {
    if (!sessionId) return;

    setIsFirstUserMessage(true);

    const fetchChatHistory = async () => {
      try {
        const response = await fetch(`/api/chat/${sessionId}`);
        if (!response.ok) {
          console.error('Failed to fetch chat history');
          return;
        }

        const data = await response.json();

        if (data.messages && Array.isArray(data.messages)) {
          setMessages(data.messages);

          const hasUserMessages = data.messages.some((msg: Message) => msg.role === 'user');
          if (hasUserMessages) {
            setIsFirstUserMessage(false);
          }
        }
      } catch (error) {
        console.error('Error fetching chat history:', error);
      }
    };

    fetchChatHistory();
  }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeTool]);

  const handleSendMessage = (message: string) => {
    if (!message.trim() || isLoading || !socketRef.current) return;

    if (isFirstUserMessage) {
      generateSessionName(message.trim());
      setIsFirstUserMessage(false);
    }

    const userMessage: Message = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);

    socketRef.current.emit('chat_message', {
      session_id: sessionId,
      message: message,
      user_id: userId || 1
    });

    setIsLoading(true);
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 rounded-lg overflow-hidden border border-gray-200 shadow-sm">
      <div className="bg-white px-4 py-3 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-800">Chat with Eunoia AI</h2>
        {sessionId && <p className="text-xs text-gray-500">Session: {sessionId.substring(0, 8)}...</p>}
      </div>

      { }
      {connectionError && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 m-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{connectionError}</p>
              <button
                className="mt-2 text-sm font-medium text-red-700 hover:text-red-600"
                onClick={() => window.location.reload()}
              >
                Refresh page
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="flex-1 p-4 overflow-y-auto">
        {messages.map((message, index) => (
          <ChatMessage
            key={index}
            role={message.role}
            content={message.content}
            isStreaming={message.isStreaming}
          />
        ))}

        {activeTool && <ToolCallNotification tool={activeTool} />}

        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t border-gray-200 bg-white">
        <ChatInput onSendMessage={handleSendMessage} disabled={isLoading || !!connectionError} />
        {isLoading && !activeTool && (
          <p className="text-xs text-gray-500 mt-2">Eunoia is thinking...</p>
        )}
      </div>
    </div>
  );
} 
