import React, { useState } from 'react';
import LogViewer from './LogViewer';

const LogToggle: React.FC = () => {
  const [isLogViewerOpen, setIsLogViewerOpen] = useState(false);

  console.log('LogToggle component rendered'); // Debug log

  return (
    <>
      <button
        onClick={() => {
          console.log('Button clicked!'); // Debug log
          setIsLogViewerOpen(true);
        }}
        className="fixed bottom-4 right-4 bg-red-600 hover:bg-red-700 text-white rounded-full p-4 shadow-2xl z-50 transition-all duration-200 hover:scale-110 border-4 border-white"
        title="View User Interaction Logs"
        style={{
          position: 'fixed',
          bottom: '16px',
          right: '16px',
          zIndex: 9999,
          backgroundColor: '#dc2626',
          color: 'white',
          borderRadius: '50%',
          padding: '16px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          border: '4px solid white'
        }}
      >
        <svg
          className="w-8 h-8"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={3}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
      </button>

      <LogViewer
        isOpen={isLogViewerOpen}
        onClose={() => setIsLogViewerOpen(false)}
      />
    </>
  );
};

export default LogToggle;
