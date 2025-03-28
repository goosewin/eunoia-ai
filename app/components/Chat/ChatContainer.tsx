import { useEffect, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import ChatInput from './ChatInput';
import ChatMessage from './ChatMessage';
import ToolCallNotification from './ToolCallNotification';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

interface ApiMessage {
  id: number;
  role: string;
  content: string;
  created_at: string;
  tool_calls?: {
    id: string;
    function: {
      name: string;
      arguments: string;
    };
  }[];
}

interface ChatContainerProps {
  sessionId: string;
  userId?: string;
}

export default function ChatContainer({ sessionId, userId }: ChatContainerProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTool, setActiveTool] = useState<string | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const socketRef = useRef<Socket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  useEffect(() => {
    // Initialize socket connection with reconnection settings
    const socketUrl = process.env.NEXT_PUBLIC_SOCKETIO_URL || (process.env.NODE_ENV === 'production' ? window.location.origin : 'http://localhost:5328');

    console.log('Connecting to socket URL:', socketUrl);

    const newSocket = io(socketUrl, {
      reconnection: true,
      reconnectionAttempts: maxReconnectAttempts,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 20000,
    });

    socketRef.current = newSocket;

    // Log connection events
    newSocket.on('connect', () => {
      console.log('Connected to WebSocket with ID:', newSocket.id);

      // Join the session room to receive messages for this session
      newSocket.emit('join', { session_id: sessionId });
      console.log('Joining session room:', sessionId);

      // Reset errors and reconnect count
      setConnectionError(null);
      reconnectAttempts.current = 0;
    });

    // Handle connection errors
    newSocket.on('connect_error', (err) => {
      console.error('Connection error:', err);
      reconnectAttempts.current += 1;

      if (reconnectAttempts.current >= maxReconnectAttempts) {
        setConnectionError('Unable to connect to server. Please refresh the page.');
      } else {
        setConnectionError(`Connection issue. Attempting to reconnect (${reconnectAttempts.current}/${maxReconnectAttempts})...`);
      }
    });

    // Handle server errors 
    newSocket.on('error', (data) => {
      console.error('Socket error:', data);
      setConnectionError(data.message || 'An error occurred with the connection');
    });

    // Handle message received confirmation
    newSocket.on('message_received', (data) => {
      console.log('Message received by server:', data);
    });

    newSocket.on('room_joined', (data) => {
      console.log('Joined room:', data);
    });

    newSocket.on('chat_message', (data: Message) => {
      console.log('Received message from server:', data);
      setMessages(prev => [...prev, data]);
      setIsLoading(false);
    });

    newSocket.on('tool_call_start', (data: { tool: string }) => {
      console.log('Tool call started:', data.tool);
      setActiveTool(data.tool);
    });

    newSocket.on('tool_call_end', () => {
      console.log('Tool call ended');
      setActiveTool(null);
    });

    // Clean up socket connection on unmount
    return () => {
      console.log('Disconnecting socket');
      newSocket.disconnect();
    };
  }, [sessionId]);

  // Fetch existing chat history
  useEffect(() => {
    const fetchChatHistory = async () => {
      try {
        const response = await fetch(`/api/chat/${sessionId}`);

        if (!response.ok) {
          throw new Error(`Server responded with status: ${response.status}`);
        }

        const data = await response.json();

        if (data.messages && Array.isArray(data.messages)) {
          const formattedMessages = data.messages
            .filter((msg: ApiMessage) => msg.role === 'user' || msg.role === 'assistant')
            .map((msg: ApiMessage) => ({
              role: msg.role as 'user' | 'assistant',
              content: msg.content,
              timestamp: msg.created_at
            }));

          setMessages(formattedMessages);
        }
      } catch (error) {
        console.error('Error fetching chat history:', error);
        setConnectionError('Failed to load chat history. Please try again later.');
      }
    };

    fetchChatHistory();
  }, [sessionId]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeTool]);

  const handleSendMessage = async (content: string) => {
    if (connectionError) {
      setConnectionError('Cannot send message while disconnected. Please refresh the page.');
      return;
    }

    // Add message to UI immediately
    const userMessage: Message = {
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      console.log('Sending message via socket:', {
        session_id: sessionId,
        message: content,
        user_id: userId
      });

      // Get current socket reference
      const currentSocket = socketRef.current;

      if (!currentSocket || !currentSocket.connected) {
        console.error('Socket not connected. Attempting to reconnect...');

        // If socket not connected, try direct HTTP only as fallback
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            session_id: sessionId,
            message: content,
            user_id: userId,
          }),
        });

        console.log('HTTP API response status:', response.status);

        if (!response.ok) {
          throw new Error(`Server responded with status: ${response.status}`);
        }

        const data = await response.json();
        console.log('HTTP API response data:', data);

        // Add response to UI manually since WebSocket isn't working
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.response || 'No response from server',
          timestamp: new Date().toISOString(),
        }]);

        setIsLoading(false);
        return;
      }

      // If socket is connected, send message through socket
      currentSocket.emit('chat_message', {
        session_id: sessionId,
        message: content,
        user_id: userId
      });

      // Also send via HTTP for reliability
      console.log('Sending message via HTTP API for reliability');
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: content,
          user_id: userId,
        }),
      });

      console.log('HTTP API response status:', response.status);

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      // If the user doesn't see a response after 10 seconds, show an error
      const timeout = setTimeout(() => {
        if (isLoading) {
          console.log('No response received after 10 seconds');
          setIsLoading(false);
          setConnectionError('No response received. Please try again.');
        }
      }, 10000);

      return () => clearTimeout(timeout);

    } catch (error) {
      console.error('Error sending message:', error);
      setIsLoading(false);
      setConnectionError('Failed to send message. Please try again.');
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-grow overflow-y-auto p-4">
        {messages.map((msg, index) => (
          <ChatMessage
            key={index}
            role={msg.role}
            content={msg.content}
            timestamp={msg.timestamp}
          />
        ))}

        {activeTool && <ToolCallNotification tool={activeTool} />}

        {connectionError && (
          <div className="p-3 bg-red-100 text-red-700 rounded-md my-2">
            <p className="text-sm font-medium">{connectionError}</p>
          </div>
        )}

        {isLoading && !activeTool && (
          <div className="flex items-center p-2">
            <div className="bg-gray-200 rounded-full p-2 animate-pulse mr-2">
              <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h.01M12 12h.01M19 12h.01M6 12a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0zm7 0a1 1 0 11-2 0 1 1 0 012 0z" />
              </svg>
            </div>
            <span className="text-sm text-gray-500">Eunoia is thinking...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="border-t p-4">
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={isLoading || !!connectionError}
        />
      </div>
    </div>
  );
} 
