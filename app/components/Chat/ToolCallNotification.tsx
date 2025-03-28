
interface ToolCallNotificationProps {
  tool: string;
}

export default function ToolCallNotification({ tool }: ToolCallNotificationProps) {
  const getToolTitle = () => {
    switch (tool) {
      case 'generate_sequence':
        return 'Generating sequence';
      case 'update_sequence':
        return 'Updating sequence';
      case 'research_industry':
        return 'Researching industry';
      default:
        return 'Processing';
    }
  };

  return (
    <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 my-4 shadow-sm">
      <div className="flex items-center space-x-3">
        <div className="relative">
          <div className="w-5 h-5 bg-indigo-100 rounded-full animate-ping absolute"></div>
          <div className="w-5 h-5 bg-indigo-500 rounded-full relative flex items-center justify-center">
            <svg className="text-white w-3 h-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
        </div>
        <div>
          <p className="font-medium text-gray-800">{getToolTitle()}...</p>
          <p className="text-sm text-gray-500">
            {tool === 'generate_sequence'
              ? 'Creating a customized outreach sequence for you'
              : 'This may take a moment'}
          </p>
        </div>
      </div>
    </div>
  );
} 
