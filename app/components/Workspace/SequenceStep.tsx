import { useState } from 'react';

interface SequenceStepProps {
  step: number;
  channel: string;
  timing: string;
  subject?: string;
  message: string;
  onEdit: (index: number, field: string, value: string) => void;
  onRemove: () => void;
}

export default function SequenceStep({
  step,
  channel,
  timing,
  subject,
  message,
  onEdit,
  onRemove,
}: SequenceStepProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleChange = (field: string, value: string) => {
    onEdit(0, field, value);
  };

  return (
    <div className="mb-4 border rounded-md overflow-hidden bg-white shadow-sm">
      <div
        className="flex items-center justify-between p-3 bg-gray-50 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-3">
          <span className="font-medium text-gray-700">Step {step}</span>
          <span className="text-sm text-gray-500">{timing}</span>
          <span className="text-sm bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
            {channel}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            type="button"
            className="text-gray-500 hover:text-gray-700"
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
          >
            {isExpanded ? (
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M8 4a.5.5 0 0 1 .5.5v7a.5.5 0 0 1-1 0v-7A.5.5 0 0 1 8 4" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4" />
              </svg>
            )}
          </button>
          <button
            type="button"
            className="text-red-500 hover:text-red-700"
            onClick={(e) => {
              e.stopPropagation();
              onRemove();
            }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z" />
              <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z" />
            </svg>
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Channel
              </label>
              <select
                value={channel}
                onChange={(e) => handleChange('channel', e.target.value)}
                className="w-full border rounded-md p-2"
              >
                <option value="Email">Email</option>
                <option value="LinkedIn">LinkedIn</option>
                <option value="Phone">Phone</option>
                <option value="SMS">SMS</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Day
              </label>
              <input
                type="number"
                onChange={(e) => handleChange('day', e.target.value)}
                className="w-full border rounded-md p-2"
                min="0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Timing Description
              </label>
              <input
                type="text"
                value={timing}
                onChange={(e) => handleChange('timing', e.target.value)}
                className="w-full border rounded-md p-2"
                placeholder="e.g., Day 3, Morning"
              />
            </div>
          </div>

          {channel === 'Email' && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Subject Line
              </label>
              <input
                type="text"
                value={subject || ''}
                onChange={(e) => handleChange('subject', e.target.value)}
                className="w-full border rounded-md p-2"
                placeholder="Enter email subject"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Message
            </label>
            <textarea
              value={message}
              onChange={(e) => handleChange('message', e.target.value)}
              className="w-full border rounded-md p-2 min-h-[160px]"
              placeholder="Enter your message here..."
            />
          </div>
        </div>
      )}
    </div>
  );
} 
