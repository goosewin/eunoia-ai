import { useState } from 'react';
import { useAgent } from '../../contexts/agent-context';

interface ChatSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ChatSidebar({ isOpen, onClose }: ChatSidebarProps) {
  const {
    sessionId,
    sessions,
    switchSession,
    createNewSession,
    renameSession,
    deleteSession,
    isRenamingSession
  } = useAgent();

  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editedName, setEditedName] = useState('');
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null);

  const sortedSessions = [...sessions].sort((a, b) =>
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const handleRenameClick = (sid: string, name: string) => {
    setEditingSessionId(sid);
    setEditedName(name);
  };

  const handleConfirmRename = (sid: string) => {
    if (editedName.trim()) {
      renameSession(sid, editedName.trim());
    }
    setEditingSessionId(null);
  };

  const handleCancelRename = () => {
    setEditingSessionId(null);
  };

  const handleDeleteClick = (sid: string) => {
    setSessionToDelete(sid);
  };

  const handleConfirmDelete = () => {
    if (sessionToDelete) {
      deleteSession(sessionToDelete);
      setSessionToDelete(null);
    }
  };

  const handleCancelDelete = () => {
    setSessionToDelete(null);
  };

  return (
    <div className={`fixed inset-y-0 left-0 z-40 w-64 bg-white border-r transform ${isOpen ? 'translate-x-0' : '-translate-x-full'} transition-transform duration-200 ease-in-out flex flex-col h-full shadow-lg`}>
      <div className="p-4 border-b flex justify-between items-center">
        <h2 className="text-lg font-semibold">Conversations</h2>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700"
          aria-label="Close sidebar"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div className="p-4">
        <button
          onClick={() => {
            createNewSession();
            onClose();
          }}
          className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-md flex items-center justify-center"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          New Conversation
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {sortedSessions.length === 0 ? (
          <div className="text-center text-gray-500 py-4">No conversations yet</div>
        ) : (
          <ul className="space-y-1">
            {sortedSessions.map((session) => (
              <li key={session.id} className={`rounded-md group ${session.id === sessionId ? 'bg-blue-50 border border-blue-100' : 'hover:bg-gray-100'}`}>
                {editingSessionId === session.id ? (
                  <div className="p-2">
                    <input
                      type="text"
                      value={editedName}
                      onChange={(e) => setEditedName(e.target.value)}
                      className="w-full p-1 border rounded-md text-sm"
                      autoFocus
                    />
                    <div className="flex justify-end space-x-1 mt-1">
                      <button
                        onClick={() => handleConfirmRename(session.id)}
                        className="text-xs py-1 px-2 bg-blue-100 hover:bg-blue-200 text-blue-800 rounded"
                        disabled={isRenamingSession}
                      >
                        Save
                      </button>
                      <button
                        onClick={handleCancelRename}
                        className="text-xs py-1 px-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded"
                        disabled={isRenamingSession}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : sessionToDelete === session.id ? (
                  <div className="p-2">
                    <p className="text-sm text-red-600 mb-1">Delete this conversation?</p>
                    <div className="flex justify-end space-x-1">
                      <button
                        onClick={handleConfirmDelete}
                        className="text-xs py-1 px-2 bg-red-100 hover:bg-red-200 text-red-800 rounded"
                      >
                        Delete
                      </button>
                      <button
                        onClick={handleCancelDelete}
                        className="text-xs py-1 px-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center p-2">
                    <button
                      onClick={() => {
                        switchSession(session.id);
                        onClose();
                      }}
                      className="flex-1 text-left overflow-hidden"
                    >
                      <span className="block truncate text-sm">{session.name || 'Unnamed Conversation'}</span>
                      <span className="block text-xs text-gray-500 truncate">
                        {new Date(session.created_at).toLocaleDateString()}
                      </span>
                    </button>
                    <div className="flex space-x-1 invisible group-hover:visible">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRenameClick(session.id, session.name || '');
                        }}
                        className="p-1 text-gray-500 hover:text-gray-700 rounded"
                        aria-label="Rename"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M12 20h9"></path>
                          <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
                        </svg>
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteClick(session.id);
                        }}
                        className="p-1 text-gray-500 hover:text-red-600 rounded"
                        aria-label="Delete"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M3 6h18"></path>
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                      </button>
                    </div>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
} 
