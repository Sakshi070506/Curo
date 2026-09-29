// Owner: Frontend Lead
// Purpose: Vite build config with React plugin + dev proxy to backend API.
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': process.env.VITE_PROXY_TARGET ?? 'http://localhost:8000'
    }
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.js',
    include: ['src/**/*.{test,spec}.{js,jsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'src/test/', 'src/main.jsx', 'src/App.jsx']
    }
  }
})