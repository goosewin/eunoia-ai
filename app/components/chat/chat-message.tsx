interface ChatMessageProps {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
  isStreaming?: boolean;
}

export default function ChatMessage({ role, content, timestamp, isStreaming = false }: ChatMessageProps) {
  const isUser = role === 'user';
  const isSystem = role === 'system';

  if (isSystem) {
    return (
      <div className="mb-4 text-center">
        <div className="inline-block max-w-[90%] px-4 py-2 rounded-lg bg-gray-100 text-gray-700 border border-gray-200">
          <p className="whitespace-pre-wrap text-sm">{content}</p>
        </div>
        {timestamp && (
          <p className="text-xs text-gray-500 mt-1">{timestamp}</p>
        )}
      </div>
    );
  }

  return (
    <div className={`mb-4 ${isUser ? 'text-right' : 'text-left'}`}>
      <div
        className={`inline-block max-w-[80%] px-4 py-2 rounded-lg ${isUser
            ? 'bg-blue-600 text-white rounded-tr-none'
            : 'bg-gray-200 text-gray-800 rounded-tl-none'
          }`}
      >
        <p className="whitespace-pre-wrap">{content}</p>
        {isStreaming && (
          <div className="mt-1 flex space-x-1">
            <div className="w-2 h-2 bg-current rounded-full animate-pulse"></div>
            <div className="w-2 h-2 bg-current rounded-full animate-pulse delay-75"></div>
            <div className="w-2 h-2 bg-current rounded-full animate-pulse delay-150"></div>
          </div>
        )}
      </div>
      {timestamp && (
        <p className="text-xs text-gray-500 mt-1">{timestamp}</p>
      )}
    </div>
  );
} 
