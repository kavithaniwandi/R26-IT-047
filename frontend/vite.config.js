import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const portalType = process.env.VITE_PORTAL_TYPE || 'default'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  cacheDir: `node_modules/.vite-${portalType}`,
  server: {
    port: 5173,
    proxy: {
      // Proxy all /api requests to the FastAPI backend
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
