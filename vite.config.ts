import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['lucide-react'], // Your existing dependency exclusion
  },
  assetsInclude: ['**/*.sql'], // Include your assets
  server: {
    fs: {
      // Allow serving files from one level up to the project root
      allow: ['..'],
    },
    proxy: {
      '/api': {
        target: 'http://localhost:5050', // Flask backend URL (updated port)
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
