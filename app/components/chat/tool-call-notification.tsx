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

  const getToolDescription = () => {
    switch (tool) {
      case 'generate_sequence':
        return 'Creating a customized outreach sequence based on our conversation';
      case 'update_sequence':
        return 'Updating the sequence with your requested changes';
      case 'research_industry':
        return 'Gathering information about industry trends and recruiting tips';
      default:
        return 'Processing your request';
    }
  };

  return (
    <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 my-4 shadow-sm animate-pulse">
      <div className="flex items-center space-x-3">
        <div className="relative">
          <div className="w-6 h-6 bg-blue-100 rounded-full animate-ping absolute"></div>
          <div className="w-6 h-6 bg-blue-500 rounded-full relative flex items-center justify-center">
            <svg className="text-white w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
        </div>
        <div className="flex-1">
          <p className="font-semibold text-blue-800">{getToolTitle()}...</p>
          <p className="text-sm text-blue-600">
            {getToolDescription()}
          </p>
        </div>
        <div className="flex-shrink-0">
          <div className="relative h-8 w-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
            <div className="absolute top-0 left-0 right-0 bottom-0 flex items-center justify-center">
              <svg className="h-4 w-4 text-blue-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
              </svg>
            </div>
          </div>
        </div>
      </div>
      <div className="mt-2 text-xs text-blue-600 font-medium">
        {tool === 'generate_sequence' && 'The sequence will appear in the workspace panel when ready'}
        {tool === 'update_sequence' && 'Changes will be reflected in the workspace panel'}
        {tool === 'research_industry' && 'Research results will be used to improve recommendations'}
      </div>
    </div>
  );
} 
