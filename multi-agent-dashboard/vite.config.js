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
      // Agent-name-based proxy routing
      // Routes /api/{agentName}/* to localhost:{port}/*
      '/api/order': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/order/, ''),
      },
      '/api/product': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/product/, ''),
      },
      '/api/inventory': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/inventory/, ''),
      },
      '/api/marketplace': {
        target: 'http://localhost:8003',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/marketplace/, ''),
      },
      '/api/payment': {
        target: 'http://localhost:8004',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/payment/, ''),
      },
      '/api/pricing': {
        target: 'http://localhost:8005',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/pricing/, ''),
      },
      '/api/carrier': {
        target: 'http://localhost:8006',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/carrier/, ''),
      },
      '/api/customer': {
        target: 'http://localhost:8007',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/customer/, ''),
      },
      '/api/warehouse': {
        target: 'http://localhost:8008',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/warehouse/, ''),
      },
      '/api/returns': {
        target: 'http://localhost:8009',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/returns/, ''),
      },
      '/api/fraud': {
        target: 'http://localhost:8010',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/fraud/, ''),
      },
      '/api/risk': {
        target: 'http://localhost:8011',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/risk/, ''),
      },
      '/api/knowledge': {
        target: 'http://localhost:8012',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/knowledge/, ''),
      },
      '/api/analytics': {
        target: 'http://localhost:8013',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/analytics/, ''),
      },
      '/api/recommendation': {
        target: 'http://localhost:8014',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/recommendation/, ''),
      },
      '/api/transport': {
        target: 'http://localhost:8015',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/transport/, ''),
      },
      '/api/documents': {
        target: 'http://localhost:8016',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/documents/, ''),
      },
      '/api/support': {
        target: 'http://localhost:8018',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/support/, ''),
      },
      '/api/communication': {
        target: 'http://localhost:8019',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/communication/, ''),
      },
      '/api/promotion': {
        target: 'http://localhost:8020',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/promotion/, ''),
      },
      '/api/aftersales': {
        target: 'http://localhost:8021',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/aftersales/, ''),
      },
      '/api/infrastructure': {
        target: 'http://localhost:8022',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/infrastructure/, ''),
      },
      '/api/monitoring': {
        target: 'http://localhost:8023',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/monitoring/, ''),
      },
      '/api/aimonitoring': {
        target: 'http://localhost:8024',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/aimonitoring/, ''),
      },
      '/api/d2c': {
        target: 'http://localhost:8026',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/d2c/, ''),
      },
      '/api/backoffice': {
        target: 'http://localhost:8027',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/backoffice/, ''),
      },
      '/api/quality': {
        target: 'http://localhost:8028',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/quality/, ''),
      },
      '/api/replenishment': {
        target: 'http://localhost:8031',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/replenishment/, ''),
      },
      '/api/inbound': {
        target: 'http://localhost:8032',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/inbound/, ''),
      },
      '/api/fulfillment': {
        target: 'http://localhost:8033',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/fulfillment/, ''),
      },
      '/api/carrierai': {
        target: 'http://localhost:8034',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/carrierai/, ''),
      },
      '/api/rma': {
        target: 'http://localhost:8035',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/rma/, ''),
      },
      '/api/advancedanalytics': {
        target: 'http://localhost:8036',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/advancedanalytics/, ''),
      },
      '/api/forecasting': {
        target: 'http://localhost:8037',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/forecasting/, ''),
      },
      '/api/international': {
        target: 'http://localhost:8038',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/international/, ''),
      },
      '/api/gateway': {
        target: 'http://localhost:8100',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/gateway/, ''),
      },
    },
  },
})
