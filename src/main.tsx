import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { initDB } from './db';
import './utils/logger'; // Initialize user interaction logging

const root = document.getElementById('root')!;

// Initialize the database before rendering
initDB()
  .then(() => {
    createRoot(root).render(
      <StrictMode>
        <App />
      </StrictMode>
    );
  })
  .catch((error) => {
    // Show a user-friendly error message
    root.innerHTML = `
      <div class="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div class="max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center">
          <h1 class="text-xl font-semibold text-gray-900 mb-4">
            Unable to Load Application
          </h1>
          <p class="text-gray-500">
            We're having trouble loading the application. Please refresh the page to try again.
          </p>
          <button
            onclick="window.location.reload()"
            class="mt-4 px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
          >
            Refresh Page
          </button>
        </div>
      </div>
    `;
    console.error('Application failed to initialize:', error);
  });