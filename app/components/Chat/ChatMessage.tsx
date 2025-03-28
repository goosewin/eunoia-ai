
interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export default function ChatMessage({ role, content, timestamp }: ChatMessageProps) {
  const isUser = role === 'user';

  return (
    <div className={`mb-4 ${isUser ? 'text-right' : 'text-left'}`}>
      <div
        className={`inline-block max-w-[80%] px-4 py-2 rounded-lg ${isUser
            ? 'bg-blue-600 text-white rounded-tr-none'
            : 'bg-gray-200 text-gray-800 rounded-tl-none'
          }`}
      >
        <p className="whitespace-pre-wrap">{content}</p>
      </div>
      {timestamp && (
        <p className="text-xs text-gray-500 mt-1">{timestamp}</p>
      )}
    </div>
  );
} 
