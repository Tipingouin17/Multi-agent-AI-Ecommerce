import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Settings,
  Warehouse,
  ShoppingCart,
  TrendingUp,
  Gavel,
  Truck,
  Package,
  DollarSign,
  Users,
  CreditCard,
  MapPin,
  Bell,
  Brain,
  GitBranch,
  RotateCcw,
  FileText,
  Search,
  CheckCircle,
  AlertCircle,
  Clock,
  ArrowRight
} from 'lucide-react';

/**
 * Settings Navigation Hub
 * 
 * Central dashboard for accessing all configuration UIs in the Multi-Agent E-commerce platform
 * 
 * Features:
 * - Categorized navigation to all 14 configuration UIs
 * - Configuration status indicators
 * - Search functionality
 * - Quick access cards
 * - Configuration completion tracking
 * - Recently accessed configurations
 * - Configuration health status
 */

const SettingsNavigationHub = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [configStatus, setConfigStatus] = useState({});
  const [loading, setLoading] = useState(true);

  // Configuration categories and items
  const configCategories = [
    {
      id: 'operations',
      name: 'Operations & Logistics',
      icon: Truck,
      color: 'blue',
      items: [
        {
          id: 'warehouse',
          name: 'Warehouse Configuration',
          description: 'Manage warehouses, locations, and inventory zones',
          icon: Warehouse,
          path: '/admin/warehouse-configuration',
          priority: 'high'
        },
        {
          id: 'carrier',
          name: 'Carrier Configuration',
          description: 'Configure shipping carriers and service levels',
          icon: Truck,
          path: '/admin/carrier-configuration',
          priority: 'high'
        },
        {
          id: 'shipping-zones',
          name: 'Shipping Zones & Rates',
          description: 'Define shipping zones and zone-based pricing',
          icon: MapPin,
          path: '/admin/shipping-zones-configuration',
          priority: 'high'
        }
      ]
    },
    {
      id: 'sales',
      name: 'Sales & Channels',
      icon: ShoppingCart,
      color: 'green',
      items: [
        {
          id: 'channel',
          name: 'Channel Configuration',
          description: 'Manage sales channels and integrations',
          icon: ShoppingCart,
          path: '/admin/channel-configuration',
          priority: 'high'
        },
        {
          id: 'marketplace',
          name: 'Marketplace Integration',
          description: 'Configure marketplace connections and monitoring',
          icon: TrendingUp,
          path: '/admin/marketplace-integration',
          priority: 'medium'
        },
        {
          id: 'product',
          name: 'Product Configuration',
          description: 'Product categories, attributes, and settings',
          icon: Package,
          path: '/admin/product-configuration',
          priority: 'medium'
        }
      ]
    },
    {
      id: 'financial',
      name: 'Financial & Compliance',
      icon: DollarSign,
      color: 'yellow',
      items: [
        {
          id: 'payment-gateway',
          name: 'Payment Gateway Configuration',
          description: 'Configure payment providers and processing',
          icon: CreditCard,
          path: '/admin/payment-gateway-configuration',
          priority: 'high'
        },
        {
          id: 'tax',
          name: 'Tax Configuration',
          description: 'Tax rules, rates, and jurisdictions',
          icon: DollarSign,
          path: '/admin/tax-configuration',
          priority: 'high'
        },
        {
          id: 'business-rules',
          name: 'Business Rules Management',
          description: 'Define business rules and policies',
          icon: Gavel,
          path: '/admin/business-rules',
          priority: 'medium'
        }
      ]
    },
    {
      id: 'customer-service',
      name: 'Customer Service',
      icon: Users,
      color: 'purple',
      items: [
        {
          id: 'return-rma',
          name: 'Return & RMA Configuration',
          description: 'Return policies and RMA workflows',
          icon: RotateCcw,
          path: '/admin/return-rma-configuration',
          priority: 'high'
        },
        {
          id: 'notifications',
          name: 'Notification Templates',
          description: 'Email, SMS, and push notification templates',
          icon: Bell,
          path: '/admin/notification-templates-configuration',
          priority: 'medium'
        }
      ]
    },
    {
      id: 'automation',
      name: 'Automation & AI',
      icon: Brain,
      color: 'indigo',
      items: [
        {
          id: 'ai-models',
          name: 'AI Model Configuration',
          description: 'Configure and monitor AI models',
          icon: Brain,
          path: '/admin/ai-model-configuration',
          priority: 'medium'
        },
        {
          id: 'workflows',
          name: 'Workflow Configuration',
          description: 'Visual workflow builder and automation',
          icon: GitBranch,
          path: '/admin/workflow-configuration',
          priority: 'high'
        },
        {
          id: 'document-templates',
          name: 'Document Templates',
          description: 'PDF, label, and document generation templates',
          icon: FileText,
          path: '/admin/document-template-configuration',
          priority: 'medium'
        }
      ]
    },
    {
      id: 'security',
      name: 'Security & Access',
      icon: Users,
      color: 'red',
      items: [
        {
          id: 'users-permissions',
          name: 'Users & Permissions',
          description: 'User management and role-based access control',
          icon: Users,
          path: '/admin/user-permissions-configuration',
          priority: 'high'
        }
      ]
    }
  ];

  // Flatten all configuration items for search
  const allConfigItems = configCategories.flatMap(category =>
    category.items.map(item => ({ ...item, category: category.name }))
  );

  // Load configuration status
  useEffect(() => {
    loadConfigStatus();
  }, []);

  const loadConfigStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/configuration-status');
      
      if (response.ok) {
        const data = await response.json();
        setConfigStatus(data.status || {});
      }
    } catch (err) {
      console.error('Error loading configuration status:', err);
    } finally {
      setLoading(false);
    }
  };

  // Filter configurations based on search query
  const filteredCategories = configCategories.map(category => ({
    ...category,
    items: category.items.filter(item =>
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(category => category.items.length > 0);

  // Get status icon and color
  const getStatusBadge = (itemId) => {
    const status = configStatus[itemId];
    
    if (!status) {
      return {
        icon: Clock,
        color: 'gray',
        text: 'Not Configured',
        bgColor: 'bg-gray-500/20',
        textColor: 'text-gray-400'
      };
    }
    
    if (status.configured && status.healthy) {
      return {
        icon: CheckCircle,
        color: 'green',
        text: 'Active',
        bgColor: 'bg-green-500/20',
        textColor: 'text-green-400'
      };
    }
    
    if (status.configured && !status.healthy) {
      return {
        icon: AlertCircle,
        color: 'yellow',
        text: 'Needs Attention',
        bgColor: 'bg-yellow-500/20',
        textColor: 'text-yellow-400'
      };
    }
    
    return {
      icon: Clock,
      color: 'gray',
      text: 'Incomplete',
      bgColor: 'bg-gray-500/20',
      textColor: 'text-gray-400'
    };
  };

  // Calculate completion percentage
  const getCompletionPercentage = () => {
    const total = allConfigItems.length;
    const configured = allConfigItems.filter(item => configStatus[item.id]?.configured).length;
    return Math.round((configured / total) * 100);
  };

  const handleNavigate = (path) => {
    navigate(path);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
          <Settings className="text-blue-400" size={36} />
          Settings & Configuration
        </h1>
        <p className="text-gray-400">
          Centralized hub for all system configuration and settings
        </p>
      </div>

      {/* Search Bar */}
      <div className="mb-8">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search configurations..."
            className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-12 pr-4 py-3 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Completion Status */}
      {!loading && (
        <div className="mb-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold text-white mb-1">
                Configuration Progress
              </h2>
              <p className="text-blue-100">
                {allConfigItems.filter(item => configStatus[item.id]?.configured).length} of {allConfigItems.length} configurations completed
              </p>
            </div>
            <div className="text-right">
              <div className="text-4xl font-bold text-white">
                {getCompletionPercentage()}%
              </div>
              <p className="text-blue-100 text-sm">Complete</p>
            </div>
          </div>
          <div className="w-full bg-blue-900/50 rounded-full h-3">
            <div
              className="bg-white rounded-full h-3 transition-all duration-500"
              style={{ width: `${getCompletionPercentage()}%` }}
            />
          </div>
        </div>
      )}

      {/* Configuration Categories */}
      {filteredCategories.map((category) => {
        const CategoryIcon = category.icon;
        
        return (
          <div key={category.id} className="mb-8">
            <div className="flex items-center gap-3 mb-4">
              <div className={`p-2 bg-${category.color}-500/20 rounded-lg`}>
                <CategoryIcon className={`text-${category.color}-400`} size={24} />
              </div>
              <h2 className="text-2xl font-bold text-white">{category.name}</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {category.items.map((item) => {
                const ItemIcon = item.icon;
                const statusBadge = getStatusBadge(item.id);
                const StatusIcon = statusBadge.icon;

                return (
                  <div
                    key={item.id}
                    onClick={() => handleNavigate(item.path)}
                    className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-all cursor-pointer group"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="p-3 bg-gray-700 rounded-lg group-hover:bg-gray-600 transition-colors">
                        <ItemIcon className="text-white" size={24} />
                      </div>
                      <div className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${statusBadge.bgColor} ${statusBadge.textColor}`}>
                        <StatusIcon size={12} />
                        <span>{statusBadge.text}</span>
                      </div>
                    </div>

                    <h3 className="text-lg font-bold text-white mb-2 group-hover:text-blue-400 transition-colors">
                      {item.name}
                    </h3>
                    <p className="text-gray-400 text-sm mb-4">
                      {item.description}
                    </p>

                    <div className="flex items-center justify-between">
                      <span className={`text-xs px-2 py-1 rounded ${
                        item.priority === 'high'
                          ? 'bg-red-500/20 text-red-400'
                          : item.priority === 'medium'
                          ? 'bg-yellow-500/20 text-yellow-400'
                          : 'bg-green-500/20 text-green-400'
                      }`}>
                        {item.priority === 'high' ? 'High Priority' : item.priority === 'medium' ? 'Medium Priority' : 'Low Priority'}
                      </span>
                      <ArrowRight className="text-gray-400 group-hover:text-blue-400 group-hover:translate-x-1 transition-all" size={20} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}

      {/* No Results */}
      {searchQuery && filteredCategories.length === 0 && (
        <div className="bg-gray-800 rounded-lg p-12 text-center border border-gray-700">
          <Search className="mx-auto mb-4 text-gray-600" size={48} />
          <h3 className="text-xl font-semibold text-gray-400 mb-2">No Results Found</h3>
          <p className="text-gray-500">
            No configurations match your search query "{searchQuery}"
          </p>
        </div>
      )}

      {/* Quick Stats */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400 text-sm">Total Configurations</span>
            <Settings className="text-gray-600" size={20} />
          </div>
          <div className="text-3xl font-bold text-white">{allConfigItems.length}</div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400 text-sm">Configured</span>
            <CheckCircle className="text-green-400" size={20} />
          </div>
          <div className="text-3xl font-bold text-green-400">
            {allConfigItems.filter(item => configStatus[item.id]?.configured).length}
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400 text-sm">Needs Attention</span>
            <AlertCircle className="text-yellow-400" size={20} />
          </div>
          <div className="text-3xl font-bold text-yellow-400">
            {allConfigItems.filter(item => configStatus[item.id]?.configured && !configStatus[item.id]?.healthy).length}
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400 text-sm">Not Configured</span>
            <Clock className="text-gray-400" size={20} />
          </div>
          <div className="text-3xl font-bold text-gray-400">
            {allConfigItems.filter(item => !configStatus[item.id]?.configured).length}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsNavigationHub;

