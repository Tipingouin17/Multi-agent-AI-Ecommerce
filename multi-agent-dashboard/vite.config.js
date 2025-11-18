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
    proxy: {
      // Proxy all API calls to localhost backend agents
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            // Dynamically route to correct agent based on path
            const path = req.url;
            let targetPort = 8000; // default to order agent
            
            // Route to appropriate agent based on API path
            if (path.includes('/products') || path.includes('/categories')) targetPort = 8001;
            else if (path.includes('/inventory')) targetPort = 8002;
            else if (path.includes('/marketplaces') && !path.includes('/analytics')) targetPort = 8003;
            else if (path.includes('/carriers') || path.includes('/shipments')) targetPort = 8004;
            else if (path.includes('/warehouse')) targetPort = 8005;
            else if (path.includes('/transport')) targetPort = 8015;
            else if (path.includes('/customers')) targetPort = 8007;
            else if (path.includes('/payments')) targetPort = 8008;
            else if (path.includes('/analytics')) targetPort = 8013;
            else if (path.includes('/recommendations')) targetPort = 8014;
            else if (path.includes('/promotions')) targetPort = 8016;
            else if (path.includes('/infrastructure') || path.includes('/system')) targetPort = 8017;
            else if (path.includes('/monitoring') || path.includes('/agents')) targetPort = 8018;
            
            // Update the target for this specific request
            proxyReq.path = path.replace('/api', '');
            proxyReq.host = 'localhost';
            proxyReq.port = targetPort;
          });
        },
      },
    },
  },
})
