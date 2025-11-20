import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './App.css'

// Admin components
import AdminLayout from './components/layouts/AdminLayout'
import AdminDashboard from './pages/admin/Dashboard'
import AgentManagement from './pages/admin/AgentManagement'
import SystemMonitoring from './pages/admin/SystemMonitoring'
import AlertsManagement from './pages/admin/AlertsManagement'
import PerformanceAnalytics from './pages/admin/PerformanceAnalytics'
import SystemConfiguration from './pages/admin/SystemConfiguration'
import { WebSocketProvider } from './contexts/WebSocketContext'
import { AuthProvider } from './contexts/AuthContext'
import ErrorBoundary from './components/ErrorBoundary'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Register from './pages/Register'
// Merchant components
import MerchantLayout from './components/layouts/MerchantLayout'
import MerchantDashboard from './pages/merchant/Dashboard'
import ProductManagement from './pages/merchant/ProductManagement'
import OrderManagement from './pages/merchant/OrderManagement'
import InventoryManagement from './pages/merchant/InventoryManagement'
import MarketplaceIntegration from './pages/merchant/MarketplaceIntegration'
import MerchantAnalytics from './pages/merchant/Analytics'
import ProductForm from './pages/merchant/ProductForm'
import OrderDetails from './pages/merchant/OrderDetails'
import BulkProductUpload from './pages/merchant/BulkProductUpload'
import OrderFulfillment from './pages/merchant/OrderFulfillment'
import ProductAnalytics from './pages/merchant/ProductAnalytics'
import ReturnsManagement from './pages/merchant/ReturnsManagement'
import ShippingManagement from './pages/merchant/ShippingManagement'
import InventoryAlerts from './pages/merchant/InventoryAlerts'
import OrderAnalytics from './pages/merchant/OrderAnalytics'
import RefundManagement from './pages/merchant/RefundManagement'
import CustomerList from './pages/merchant/CustomerList'
import CustomerProfile from './pages/merchant/CustomerProfile'
import CampaignManagement from './pages/merchant/CampaignManagement'
import PromotionManager from './pages/merchant/PromotionManager'
import ReviewManagement from './pages/merchant/ReviewManagement'
import MarketingAnalytics from './pages/merchant/MarketingAnalytics'
import CustomerSegmentation from './pages/merchant/CustomerSegmentation'
import LoyaltyProgram from './pages/merchant/LoyaltyProgram'
import EmailCampaignBuilder from './pages/merchant/EmailCampaignBuilder'
import MarketingAutomation from './pages/merchant/MarketingAutomation'
import Offers from './pages/merchant/Offers'
import OfferWizard from './pages/merchant/OfferWizard'
import Campaigns from './pages/merchant/Campaigns'
import Suppliers from './pages/merchant/Suppliers'
import StoreSettings from './pages/merchant/StoreSettings'
import PaymentSettings from './pages/merchant/PaymentSettings'
import ShippingSettings from './pages/merchant/ShippingSettings'
import TaxSettings from './pages/merchant/TaxSettings'
import EmailTemplates from './pages/merchant/EmailTemplates'
import NotificationSettings from './pages/merchant/NotificationSettings'
import DomainSettings from './pages/merchant/DomainSettings'
import APISettings from './pages/merchant/APISettings'
import FinancialDashboard from './pages/merchant/FinancialDashboard'
import SalesReports from './pages/merchant/SalesReports'
import ProfitLossStatement from './pages/merchant/ProfitLossStatement'
import RevenueAnalytics from './pages/merchant/RevenueAnalytics'
import ExpenseTracking from './pages/merchant/ExpenseTracking'
import TaxReports from './pages/merchant/TaxReports'
import SalesRevenueDashboard from './pages/merchant/SalesRevenueDashboard'
import OrderManagementDashboard from './pages/merchant/OrderManagementDashboard'
import InventoryDashboard from './pages/merchant/InventoryDashboard'
import FinancialOverviewDashboard from './pages/merchant/FinancialOverviewDashboard'
import CustomerAnalyticsDashboard from './pages/merchant/CustomerAnalyticsDashboard'
import ProductAnalyticsDashboard from './pages/merchant/ProductAnalyticsDashboard'
import MarketingAnalyticsDashboard from './pages/merchant/MarketingAnalyticsDashboard'
import OperationalMetricsDashboard from './pages/merchant/OperationalMetricsDashboard';
import ReplenishmentDashboard from './pages/merchant/ReplenishmentDashboard';
import InboundManagementDashboard from './pages/admin/InboundManagementDashboard';
import FulfillmentDashboard from './pages/admin/FulfillmentDashboard';
import CarrierDashboard from './pages/admin/CarrierDashboard';
import RMADashboard from './pages/admin/RMADashboard';
import AnalyticsDashboard from './pages/admin/AnalyticsDashboard';
import ForecastingDashboard from './pages/admin/ForecastingDashboard';
import InternationalShippingDashboard from './pages/admin/InternationalShippingDashboard';

// Customer components
import CustomerLayout from './components/layouts/CustomerLayout'
import Home from './pages/customer/Home'
import ProductCatalog from './pages/customer/ProductCatalog'
import ProductDetails from './pages/customer/ProductDetails'
import ShoppingCart from './pages/customer/ShoppingCart'
import OrderTracking from './pages/customer/OrderTracking'
import OrdersList from './pages/customer/OrdersList'
import Account from './pages/customer/Account'
import Checkout from './pages/customer/Checkout'
import OrderConfirmation from './pages/customer/OrderConfirmation'
import SearchResults from './pages/customer/SearchResults'
import OrderDetail from './pages/customer/OrderDetail'
import AccountSettings from './pages/customer/AccountSettings'
import AddressBook from './pages/customer/AddressBook'
import Wishlist from './pages/customer/Wishlist'
import CustomerReviews from './pages/customer/CustomerReviews'
import Help from './pages/customer/Help'

// Database test component
import DatabaseTest from './components/DatabaseTest'


// Interface selector component with database status
function InterfaceSelector({ onSelect, databaseStatus }) {
  const interfaceOptions = [
    {
      id: 'admin',
      title: 'System Administrator',
      description: 'Monitor and manage the entire multi-agent e-commerce ecosystem with real-time database insights',
      color: 'bg-blue-500',
      features: [
        'Real-time AI Agent Monitoring',
        'Database Performance Analytics', 
        'Live Error Management & Alerts',
        'System Configuration Management'
      ]
    },
    {
      id: 'merchant', 
      title: 'Merchant Portal',
      description: 'Manage products, orders, and marketplace integrations with live database synchronization',
      color: 'bg-green-500',
      features: [
        'Live Product Catalog Management',
        'Multi-Marketplace Integration',
        'Real-time Order Processing',
        'Dynamic Inventory Management'
      ]
    },
    {
      id: 'customer',
      title: 'Customer Experience', 
      description: 'Browse products, place orders, and track deliveries with real-time data updates',
      color: 'bg-purple-500',
      features: [
        'Live Product Discovery & Search',
        'Real-time Shopping Cart',
        'Live Order Tracking & History',
        'Dynamic Account Management'
      ]
    },
    {
      id: 'database-test',
      title: 'Database Integration Test',
      description: 'Test and monitor database connectivity and data synchronization',
      color: 'bg-orange-500',
      features: [
        'Database Connection Testing',
        'Agent Health Monitoring',
        'Real-time Data Validation',
        'Performance Metrics'
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="max-w-7xl w-full">
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Multi-Agent E-commerce Platform
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-6">
            Choose your interface to access the world's most advanced AI-powered e-commerce system
          </p>
          
          {/* Database Status Indicator */}
          <div className="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium mb-6">
            <div className={`w-3 h-3 rounded-full mr-2 ${
              databaseStatus.connected ? 'bg-green-500' : 'bg-red-500'
            }`}></div>
            <span className={databaseStatus.connected ? 'text-green-700' : 'text-red-700'}>
              Database: {databaseStatus.connected ? 'Connected' : 'Disconnected'}
            </span>
            {databaseStatus.healthyAgents > 0 && (
              <span className="ml-2 text-gray-600">
                ({databaseStatus.healthyAgents}/{databaseStatus.totalAgents} agents healthy)
              </span>
            )}
          </div>
          
          <div className="text-sm text-gray-500 mb-8">
            <strong>Database-First Architecture:</strong> All interfaces use real database data. 
            Mock data fallbacks are disabled to ensure data integrity.
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {interfaceOptions.map((option) => (
            <div 
              key={option.id}
              className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300"
            >
              <div className={`${option.color} h-2`}></div>
              <div className="p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-2">{option.title}</h2>
                <p className="text-gray-600 mb-4 text-sm">{option.description}</p>
                
                <div className="mb-6">
                  <h3 className="text-xs font-medium text-gray-500 mb-2">Key Features</h3>
                  <ul className="space-y-1">
                    {option.features.map((feature, index) => (
                      <li key={index} className="flex items-center">
                        <svg className="h-3 w-3 text-green-500 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                        </svg>
                        <span className="text-gray-700 text-xs">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                
                <button
                  onClick={() => onSelect(option.id)}
                  className={`w-full py-2 px-4 rounded-md text-white font-medium text-sm ${option.color} hover:opacity-90 transition-opacity duration-300`}
                >
                  Access {option.title}
                </button>
              </div>
            </div>
          ))}
        </div>
        
        {!databaseStatus.connected && (
          <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">
                  Database Connection Warning
                </h3>
                <div className="mt-2 text-sm text-yellow-700">
                  <p>
                    Some or all backend services are currently unavailable. 
                    Please ensure all microservice agents are running and connected to the database.
                    You can still access the interfaces, but data may be limited.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function App() {
  const [selectedInterface, setSelectedInterface] = useState(
    localStorage.getItem('selectedInterface') || null
  );
  const [databaseStatus, setDatabaseStatus] = useState({
    connected: false,
    healthyAgents: 0,
    totalAgents: 5,
    lastChecked: null
  });

  // Check database status on app load
  useEffect(() => {
    checkDatabaseStatus();
    // Check database status every 30 seconds
    const interval = setInterval(checkDatabaseStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkDatabaseStatus = async () => {
    try {
      const agents = [
        { name: 'Monitoring', port: 8014 },
        { name: 'Product', port: 8002 },
        { name: 'Order', port: 8001 },
        { name: 'Inventory', port: 8003 },
        { name: 'Communication', port: 8008 }
      ];

      const healthChecks = await Promise.allSettled(
        agents.map(async (agent) => {
          try {
            const response = await fetch(`http://localhost:${agent.port}/health`, {
              method: 'GET',
              timeout: 5000
            });
            return response.ok;
          } catch {
            return false;
          }
        })
      );

      const healthyCount = healthChecks.filter(result => 
        result.status === 'fulfilled' && result.value === true
      ).length;

      setDatabaseStatus({
        connected: healthyCount > 0,
        healthyAgents: healthyCount,
        totalAgents: agents.length,
        lastChecked: new Date().toISOString()
      });
    } catch (error) {
      console.error('Database status check failed:', error);
      setDatabaseStatus(prev => ({
        ...prev,
        connected: false,
        healthyAgents: 0,
        lastChecked: new Date().toISOString()
      }));
    }
  };

  const handleInterfaceSelect = (interfaceType) => {
    setSelectedInterface(interfaceType);
    localStorage.setItem('selectedInterface', interfaceType);
  };

  const handleInterfaceReset = () => {
    setSelectedInterface(null);
    localStorage.removeItem('selectedInterface');
    // Refresh database status when returning to selector
    checkDatabaseStatus();
  };

  return (
    <AuthProvider>
      <WebSocketProvider>
      <BrowserRouter>
        {/* Public routes */}
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          {!selectedInterface && (
            <Route path="*" element={<Navigate to="/login" replace />} />
          )}
        </Routes>

        {selectedInterface === 'admin' && (
          <Routes>
            <Route path="/" element={<ProtectedRoute allowedRoles={['admin']}><AdminLayout onInterfaceReset={handleInterfaceReset} /></ProtectedRoute>}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<ErrorBoundary><AdminDashboard /></ErrorBoundary>} />
              <Route path="/agents" element={<ErrorBoundary><AgentManagement /></ErrorBoundary>} />
              <Route path="/monitoring" element={<ErrorBoundary><SystemMonitoring /></ErrorBoundary>} />
              <Route path="/alerts" element={<ErrorBoundary><AlertsManagement /></ErrorBoundary>} />
              <Route path="/analytics" element={<ErrorBoundary><PerformanceAnalytics /></ErrorBoundary>} />
              <Route path="/configuration" element={<ErrorBoundary><SystemConfiguration /></ErrorBoundary>} />
              <Route path="/inbound" element={<ErrorBoundary><InboundManagementDashboard /></ErrorBoundary>} />
              <Route path="/fulfillment" element={<ErrorBoundary><FulfillmentDashboard /></ErrorBoundary>} />
              <Route path="/carriers" element={<ErrorBoundary><CarrierDashboard /></ErrorBoundary>} />
              <Route path="/rma" element={<ErrorBoundary><RMADashboard /></ErrorBoundary>} />
              <Route path="/advanced-analytics" element={<ErrorBoundary><AnalyticsDashboard /></ErrorBoundary>} />
              <Route path="/forecasting" element={<ErrorBoundary><ForecastingDashboard /></ErrorBoundary>} />
              <Route path="/international" element={<ErrorBoundary><InternationalShippingDashboard /></ErrorBoundary>} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Route>
          </Routes>
        )}
        
        {selectedInterface === 'merchant' && (
          <Routes>
            <Route path="/" element={<ProtectedRoute allowedRoles={['merchant']}><MerchantLayout onInterfaceReset={handleInterfaceReset} /></ProtectedRoute>}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<ErrorBoundary><MerchantDashboard /></ErrorBoundary>} />
              <Route path="/products" element={<ErrorBoundary><ProductManagement /></ErrorBoundary>} />
              <Route path="/products/new" element={<ErrorBoundary><ProductForm /></ErrorBoundary>} />
              <Route path="/products/:id/edit" element={<ErrorBoundary><ProductForm /></ErrorBoundary>} />
              <Route path="/products/bulk-upload" element={<ErrorBoundary><BulkProductUpload /></ErrorBoundary>} />
              <Route path="/products/analytics" element={<ErrorBoundary><ProductAnalytics /></ErrorBoundary>} />
              <Route path="/orders" element={<ErrorBoundary><OrderManagement /></ErrorBoundary>} />
              <Route path="/orders/:id" element={<ErrorBoundary><OrderDetails /></ErrorBoundary>} />
              <Route path="/orders/:id/fulfill" element={<ErrorBoundary><OrderFulfillment /></ErrorBoundary>} />
              <Route path="/returns" element={<ErrorBoundary><ReturnsManagement /></ErrorBoundary>} />
              <Route path="/shipping" element={<ErrorBoundary><ShippingManagement /></ErrorBoundary>} />
              <Route path="/inventory/alerts" element={<ErrorBoundary><InventoryAlerts /></ErrorBoundary>} />
              <Route path="/orders/analytics" element={<ErrorBoundary><OrderAnalytics /></ErrorBoundary>} />
              <Route path="/refunds" element={<ErrorBoundary><RefundManagement /></ErrorBoundary>} />
              <Route path="/customers" element={<ErrorBoundary><CustomerList /></ErrorBoundary>} />
              <Route path="/customers/:id" element={<ErrorBoundary><CustomerProfile /></ErrorBoundary>} />
              <Route path="/marketing/campaigns" element={<ErrorBoundary><CampaignManagement /></ErrorBoundary>} />
              <Route path="/marketing/promotions" element={<ErrorBoundary><PromotionManager /></ErrorBoundary>} />
              <Route path="/marketing/reviews" element={<ErrorBoundary><ReviewManagement /></ErrorBoundary>} />
              <Route path="/marketing/analytics" element={<ErrorBoundary><MarketingAnalytics /></ErrorBoundary>} />
              <Route path="/customers/segments" element={<ErrorBoundary><CustomerSegmentation /></ErrorBoundary>} />
              <Route path="/marketing/loyalty" element={<ErrorBoundary><LoyaltyProgram /></ErrorBoundary>} />
              <Route path="/marketing/campaigns/new" element={<ErrorBoundary><EmailCampaignBuilder /></ErrorBoundary>} />
              <Route path="/marketing/automation" element={<ErrorBoundary><MarketingAutomation /></ErrorBoundary>} />
              <Route path="/inventory" element={<ErrorBoundary><InventoryManagement /></ErrorBoundary>} />
              <Route path="/marketplaces" element={<ErrorBoundary><MarketplaceIntegration /></ErrorBoundary>} />
              <Route path="/offers" element={<ErrorBoundary><Offers /></ErrorBoundary>} />
              <Route path="/offers/new" element={<ErrorBoundary><OfferWizard /></ErrorBoundary>} />
              <Route path="/campaigns" element={<ErrorBoundary><Campaigns /></ErrorBoundary>} />
              <Route path="/suppliers" element={<ErrorBoundary><Suppliers /></ErrorBoundary>} />
              <Route path="/analytics" element={<ErrorBoundary><MerchantAnalytics /></ErrorBoundary>} />
              <Route path="/analytics/sales-revenue" element={<ErrorBoundary><SalesRevenueDashboard /></ErrorBoundary>} />
              <Route path="/analytics/orders" element={<ErrorBoundary><OrderManagementDashboard /></ErrorBoundary>} />
              <Route path="/analytics/inventory" element={<ErrorBoundary><InventoryDashboard /></ErrorBoundary>} />
              <Route path="/analytics/financial" element={<ErrorBoundary><FinancialOverviewDashboard /></ErrorBoundary>} />
              <Route path="/analytics/customers" element={<ErrorBoundary><CustomerAnalyticsDashboard /></ErrorBoundary>} />
              <Route path="/analytics/products" element={<ErrorBoundary><ProductAnalyticsDashboard /></ErrorBoundary>} />
              <Route path="/analytics/marketing" element={<ErrorBoundary><MarketingAnalyticsDashboard /></ErrorBoundary>} />
              <Route path="/analytics/operations" element={<ErrorBoundary><OperationalMetricsDashboard /></ErrorBoundary>} />
              <Route path="/inventory/replenishment" element={<ErrorBoundary><ReplenishmentDashboard /></ErrorBoundary>} />
              <Route path="/settings/general" element={<ErrorBoundary><StoreSettings /></ErrorBoundary>} />
              <Route path="/settings/payments" element={<ErrorBoundary><PaymentSettings /></ErrorBoundary>} />
              <Route path="/settings/shipping" element={<ErrorBoundary><ShippingSettings /></ErrorBoundary>} />
              <Route path="/settings/taxes" element={<ErrorBoundary><TaxSettings /></ErrorBoundary>} />
              <Route path="/settings/emails" element={<ErrorBoundary><EmailTemplates /></ErrorBoundary>} />
              <Route path="/settings/notifications" element={<ErrorBoundary><NotificationSettings /></ErrorBoundary>} />
              <Route path="/settings/domain" element={<ErrorBoundary><DomainSettings /></ErrorBoundary>} />
              <Route path="/settings/api" element={<ErrorBoundary><APISettings /></ErrorBoundary>} />
              <Route path="/financial/dashboard" element={<ErrorBoundary><FinancialDashboard /></ErrorBoundary>} />
              <Route path="/financial/sales-reports" element={<ErrorBoundary><SalesReports /></ErrorBoundary>} />
              <Route path="/financial/profit-loss" element={<ErrorBoundary><ProfitLossStatement /></ErrorBoundary>} />
              <Route path="/financial/revenue-analytics" element={<ErrorBoundary><RevenueAnalytics /></ErrorBoundary>} />
              <Route path="/financial/expenses" element={<ErrorBoundary><ExpenseTracking /></ErrorBoundary>} />
              <Route path="/financial/tax-reports" element={<ErrorBoundary><TaxReports /></ErrorBoundary>} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Route>
          </Routes>
        )}
        
        {selectedInterface === 'customer' && (
          <Routes>
            <Route path="/" element={<ProtectedRoute allowedRoles={['customer']}><CustomerLayout onInterfaceReset={handleInterfaceReset} /></ProtectedRoute>}>
              <Route index element={<Home />} />
              <Route path="/products" element={<ErrorBoundary><ProductCatalog /></ErrorBoundary>} />
              <Route path="/products/:productId" element={<ErrorBoundary><ProductDetails /></ErrorBoundary>} />
              <Route path="/cart" element={<ErrorBoundary><ShoppingCart /></ErrorBoundary>} />
              <Route path="/orders" element={<ErrorBoundary><OrdersList /></ErrorBoundary>} />
              <Route path="/account" element={<ErrorBoundary><Account /></ErrorBoundary>} />
              <Route path="/checkout" element={<ErrorBoundary><Checkout /></ErrorBoundary>} />
              <Route path="/order-confirmation/:orderId" element={<ErrorBoundary><OrderConfirmation /></ErrorBoundary>} />
              <Route path="/search" element={<ErrorBoundary><SearchResults /></ErrorBoundary>} />
              <Route path="/account/orders/:orderId" element={<ErrorBoundary><OrderDetail /></ErrorBoundary>} />
              <Route path="/account/settings" element={<ErrorBoundary><AccountSettings /></ErrorBoundary>} />
              <Route path="/account/addresses" element={<ErrorBoundary><AddressBook /></ErrorBoundary>} />
              <Route path="/account/wishlist" element={<ErrorBoundary><Wishlist /></ErrorBoundary>} />
              <Route path="/account/reviews" element={<ErrorBoundary><CustomerReviews /></ErrorBoundary>} />
              <Route path="/help" element={<ErrorBoundary><Help /></ErrorBoundary>} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        )}
        
        {selectedInterface === 'database-test' && (
          <DatabaseTest onReset={handleInterfaceReset} />
        )}
      </BrowserRouter>
      </WebSocketProvider>
    </AuthProvider>
  );
}

export default App;
