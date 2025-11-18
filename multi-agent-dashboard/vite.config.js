import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(),tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: true, // Listen on all addresses
    allowedHosts: [
      '.ngrok-free.app', // Allow all ngrok free domains
      '.ngrok.io',       // Allow all ngrok paid domains
      'localhost',       // Allow localhost
    ],
  },
})
