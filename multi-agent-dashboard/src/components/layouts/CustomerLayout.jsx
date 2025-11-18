import { useState, useEffect } from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Home,
  Search,
  ShoppingCart,
  Package,
  User,
  Heart,
  Menu,
  X,
  LogOut,
  Bell
} from 'lucide-react'
import UserProfileDropdown from '../shared/UserProfileDropdown'
import NotificationsDropdown from '../shared/NotificationsDropdown'
import { useUser } from '../../contexts/UserContext'
import { useAuth } from '../../contexts/AuthContext'

const CustomerLayout = ({ onInterfaceReset }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [showProfileMenu, setShowProfileMenu] = useState(false)
  const [showNotifications, setShowNotifications] = useState(false)
  const { user } = useUser()
  const { logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }
  
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
    { name: 'Home', href: '/home', icon: Home },
    { name: 'Products', href: '/products', icon: Search },
    { name: 'Cart', href: '/cart', icon: ShoppingCart },
    { name: 'Orders', href: '/orders', icon: Package },
    { name: 'Account', href: '/account', icon: User },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center space-x-4">
              <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center">
                <ShoppingCart className="w-5 h-5 text-white" />
              </div>
              <div className="hidden sm:block">
                <h1 className="text-xl font-bold text-gray-900">E-Shop</h1>
                <p className="text-xs text-gray-500">Multi-Agent Platform</p>
              </div>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex space-x-8">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.href
                
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'text-purple-600 bg-purple-50'
                        : 'text-gray-600 hover:text-purple-600 hover:bg-purple-50'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </Link>
                )
              })}
            </nav>

            {/* Right Side Actions */}
            <div className="flex items-center space-x-4">
              {/* Search Bar */}
              <div className="hidden lg:block relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search products..."
                  className="pl-10 pr-4 py-2 w-64 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>

              {/* Wishlist */}
              <Button variant="ghost" size="sm" className="relative">
                <Heart className="w-5 h-5" />
                <Badge className="absolute -top-1 -right-1 w-5 h-5 p-0 flex items-center justify-center bg-red-500 text-white text-xs">
                  3
                </Badge>
              </Button>

              {/* Cart */}
              <Button variant="ghost" size="sm" className="relative">
                <ShoppingCart className="w-5 h-5" />
                <Badge className="absolute -top-1 -right-1 w-5 h-5 p-0 flex items-center justify-center bg-purple-500 text-white text-xs">
                  2
                </Badge>
              </Button>

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
                  <Badge className="absolute -top-1 -right-1 w-5 h-5 p-0 flex items-center justify-center bg-blue-500 text-white text-xs">
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

              {/* Mobile Menu Button */}
              <Button
                variant="ghost"
                size="sm"
                className="md:hidden"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </Button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden border-t border-gray-200 bg-white"
          >
            <div className="px-4 py-2 space-y-1">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.href
                
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium ${
                      isActive
                        ? 'text-purple-600 bg-purple-50'
                        : 'text-gray-600 hover:text-purple-600 hover:bg-purple-50'
                    }`}
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </Link>
                )
              })}
              
              {/* Mobile Search */}
              <div className="px-3 py-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="Search products..."
                    className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Switch Interface */}
              <Button
                variant="ghost"
                onClick={handleLogout}
                className="w-full justify-start text-gray-600 hover:text-purple-600 hover:bg-purple-50"
              >
                <LogOut className="w-4 h-4 mr-3" />
                Logout
              </Button>
              <Button
                variant="ghost"
                onClick={onInterfaceReset}
                className="w-full justify-start text-gray-600 hover:text-purple-600 hover:bg-purple-50 text-xs"
              >
                Switch Interface
              </Button>
            </div>
          </motion.div>
        )}
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center">
                  <ShoppingCart className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-lg font-semibold">E-Shop</h3>
              </div>
              <p className="text-gray-400 text-sm">
                Your trusted multi-agent e-commerce platform with AI-powered shopping experience.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Shop</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><Link to="/products" className="hover:text-white">All Products</Link></li>
                <li><Link to="/categories" className="hover:text-white">Categories</Link></li>
                <li><Link to="/deals" className="hover:text-white">Special Deals</Link></li>
                <li><Link to="/new" className="hover:text-white">New Arrivals</Link></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Support</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><Link to="/help" className="hover:text-white">Help Center</Link></li>
                <li><Link to="/contact" className="hover:text-white">Contact Us</Link></li>
                <li><Link to="/shipping" className="hover:text-white">Shipping Info</Link></li>
                <li><Link to="/returns" className="hover:text-white">Returns</Link></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">Account</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><Link to="/account" className="hover:text-white">My Account</Link></li>
                <li><Link to="/orders" className="hover:text-white">Order History</Link></li>
                <li><Link to="/wishlist" className="hover:text-white">Wishlist</Link></li>
                <li><Button onClick={handleLogout} className="text-gray-400 hover:text-white p-0 h-auto font-normal text-sm">Logout</Button></li>
                <li><Button onClick={onInterfaceReset} className="text-gray-400 hover:text-white p-0 h-auto font-normal text-sm">Switch Interface</Button></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm text-gray-400">
            <p>&copy; 2024 Multi-Agent E-commerce Platform. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default CustomerLayout
