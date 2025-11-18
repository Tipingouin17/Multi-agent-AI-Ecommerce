import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// Agent port mapping
const AGENT_PORTS = {
  order: 8000,
  product: 8001,
  inventory: 8002,
  marketplace: 8003,
  payment: 8004,
  pricing: 8005,
  carrier: 8006,
  customer: 8007,
  warehouse: 8008,
  returns: 8009,
  fraud: 8010,
  risk: 8011,
  knowledge: 8012,
  analytics: 8013,
  recommendation: 8014,
  transport: 8015,
  documents: 8016,
  support: 8018,
  communication: 8019,
  promotion: 8020,
  aftersales: 8021,
  infrastructure: 8022,
  monitoring: 8023,
  aimonitoring: 8024,
  d2c: 8026,
  backoffice: 8027,
  quality: 8028,
  replenishment: 8031,
  inbound: 8032,
  fulfillment: 8033,
  carrierai: 8034,
  rma: 8035,
  advancedanalytics: 8036,
  forecasting: 8037,
  international: 8038,
  gateway: 8100,
};

// Create proxy configuration for each agent
const proxyConfig = {};
Object.entries(AGENT_PORTS).forEach(([agentName, port]) => {
  proxyConfig[`/api/${agentName}`] = {
    target: `http://localhost:${port}`,
    changeOrigin: true,
    rewrite: (path) => {
      // Simply strip /api/{agentName} from the path
      // /api/product/health -> /health
      // /api/product/api/products -> /api/products
      return path.replace(`/api/${agentName}`, '');
    },
  };
});

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
    proxy: proxyConfig,
  },
})
