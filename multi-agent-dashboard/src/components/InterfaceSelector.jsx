import { useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Shield, 
  Store, 
  ShoppingBag, 
  BarChart3, 
  Settings, 
  Users
} from 'lucide-react'

const InterfaceSelector = ({ onSelect }) => {
  const [hoveredItem, setHoveredItem] = useState(null)

  const interfaceOptions = [
    {
      id: 'admin',
      title: 'System Administrator',
      description: 'Monitor and manage the entire multi-agent e-commerce ecosystem',
      icon: Shield,
      color: 'bg-blue-500',
      features: [
        'AI Agent Monitoring',
        'System Performance Analytics', 
        'Error Management & Alerts',
        'Configuration Management'
      ]
    },
    {
      id: 'merchant', 
      title: 'Merchant Portal',
      description: 'Manage products, orders, and marketplace integrations efficiently',
      icon: Store,
      color: 'bg-green-500',
      features: [
        'Product Catalog Management',
        'Multi-Marketplace Integration',
        'Order Processing & Fulfillment',
        'Inventory Management'
      ]
    },
    {
      id: 'customer',
      title: 'Customer Experience', 
      description: 'Browse products, place orders, and track deliveries seamlessly',
      icon: ShoppingBag,
      color: 'bg-purple-500',
      features: [
        'Product Discovery & Search',
        'Shopping Cart & Checkout',
        'Order Tracking & History',
        'Account Management'
      ]
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-6xl w-full">
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Multi-Agent E-commerce Platform
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Choose your interface to access the world's most advanced AI-powered e-commerce ecosystem
          </p>
          <div className="flex items-center justify-center gap-2 mt-6">
            <Badge variant="secondary">
              <BarChart3 className="w-4 h-4 mr-1" />
              Real-time Analytics
            </Badge>
            <Badge variant="secondary">
              <Settings className="w-4 h-4 mr-1" />
              AI-Powered
            </Badge>
            <Badge variant="secondary">
              <Users className="w-4 h-4 mr-1" />
              Multi-Agent
            </Badge>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {interfaceOptions.map((item, index) => {
            const Icon = item.icon
            return (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.2 }}
                onHoverStart={() => setHoveredItem(item.id)}
                onHoverEnd={() => setHoveredItem(null)}
              >
                <Card className={`h-full transition-all duration-300 cursor-pointer ${
                  hoveredItem === item.id 
                    ? 'border-blue-500 shadow-2xl scale-105' 
                    : 'shadow-lg hover:shadow-xl'
                }`}>
                  <CardHeader className="text-center">
                    <div className={`w-16 h-16 ${item.color} rounded-full flex items-center justify-center mx-auto mb-4`}>
                      <Icon className="w-8 h-8 text-white" />
                    </div>
                    <CardTitle className="text-2xl">{item.title}</CardTitle>
                    <CardDescription>{item.description}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <ul className="space-y-2">
                      {item.features.map((feature, idx) => (
                        <li key={idx} className="flex items-center text-sm">
                          <div className="w-2 h-2 bg-blue-500 rounded-full mr-3" />
                          {feature}
                        </li>
                      ))}
                    </ul>
                    <Button 
                      onClick={() => onSelect(item.id)}
                      className="w-full"
                    >
                      Access {item.title}
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default InterfaceSelector
