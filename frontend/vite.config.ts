import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8003',
        changeOrigin: true,
      },
      '/session': {
        target: 'http://localhost:8003',
        changeOrigin: true,
      },
      '/export': {
        target: 'http://localhost:8003',
        changeOrigin: true,
      },
      '/socket.io': {
        target: 'http://localhost:8003',
        changeOrigin: true,
        ws: true,
      },
    },
  },
})
