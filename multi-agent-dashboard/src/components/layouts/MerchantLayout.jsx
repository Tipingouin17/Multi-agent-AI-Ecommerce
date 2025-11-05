import { useState, useEffect } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  LayoutDashboard,
  Package,
  ShoppingCart,
  Warehouse,
  Store,
  BarChart3,
  Menu,
  X,
  LogOut,
  Bell,
  Search,
  User
} from 'lucide-react'
import UserProfileDropdown from '../shared/UserProfileDropdown'
import NotificationsDropdown from '../shared/NotificationsDropdown'
import { useUser } from '../../contexts/UserContext'

const MerchantLayout = ({ onInterfaceReset }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [showProfileMenu, setShowProfileMenu] = useState(false)
  const [showNotifications, setShowNotifications] = useState(false)
  const { user } = useUser()
  const location = useLocation()
  
  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!event.target.closest('.dropdown-container')) {
        setShowProfileMenu(false)
        setShowNotifications(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Products', href: '/products', icon: Package },
    { name: 'Orders', href: '/orders', icon: ShoppingCart },
    { name: 'Inventory', href: '/inventory', icon: Warehouse },
    { name: 'Marketplaces', href: '/marketplaces', icon: Store },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <motion.div
        initial={false}
        animate={{ width: sidebarOpen ? 256 : 64 }}
        className="fixed inset-y-0 left-0 z-50 bg-green-900 shadow-xl"
      >
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-green-800">
            {sidebarOpen && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-center space-x-2"
              >
                <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center">
                  <Store className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-white font-semibold text-sm">Merchant Portal</h1>
                  <p className="text-green-400 text-xs">E-commerce Management</p>
                </div>
              </motion.div>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="text-green-400 hover:text-white hover:bg-green-800"
            >
              {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </Button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-2 py-4 space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.href
              
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-green-600 text-white'
                      : 'text-green-300 hover:bg-green-800 hover:text-white'
                  }`}
                >
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  {sidebarOpen && (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="ml-3"
                    >
                      {item.name}
                    </motion.span>
                  )}
                </Link>
              )
            })}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-green-800">
            <Button
              variant="ghost"
              onClick={onInterfaceReset}
              className="w-full justify-start text-green-400 hover:text-white hover:bg-green-800"
            >
              <LogOut className="w-4 h-4" />
              {sidebarOpen && <span className="ml-3">Switch Interface</span>}
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Main Content */}
      <div className={`transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-16'}`}>
        {/* Top Header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Merchant Dashboard</h2>
                <p className="text-gray-600">Manage your products, orders, and marketplace integrations</p>
              </div>
              
              <div className="flex items-center space-x-4">
                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="Search products..."
                    className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>

                {/* Notifications */}
                <div className="relative dropdown-container">
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="relative"
                    onClick={() => {
                      setShowNotifications(!showNotifications)
                      setShowProfileMenu(false)
                    }}
                  >
                    <Bell className="w-5 h-5" />
                    <Badge className="absolute -top-1 -right-1 w-5 h-5 p-0 flex items-center justify-center bg-green-500 text-white text-xs">
                      2
                    </Badge>
                  </Button>
                  {showNotifications && (
                    <NotificationsDropdown onClose={() => setShowNotifications(false)} />
                  )}
                </div>

                {/* User Menu */}
                <div className="relative dropdown-container">
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={() => {
                      setShowProfileMenu(!showProfileMenu)
                      setShowNotifications(false)
                    }}
                  >
                    <User className="w-5 h-5" />
                  </Button>
                  {showProfileMenu && (
                    <UserProfileDropdown onClose={() => setShowProfileMenu(false)} />
                  )}
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default MerchantLayout
