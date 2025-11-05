import { useState, useEffect } from 'react';
import { Bell, Package, AlertTriangle, Info, CheckCircle, X } from 'lucide-react';

const NotificationsDropdown = ({ onClose }) => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate fetching notifications
    // In a real app, you'd fetch from API: GET /api/notifications
    setTimeout(() => {
      const mockNotifications = [
        {
          id: 1,
          type: 'order',
          title: 'New Order Received',
          message: 'Order #12345 has been placed by John Doe',
          is_read: false,
          created_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(), // 5 min ago
        },
        {
          id: 2,
          type: 'alert',
          title: 'Low Stock Alert',
          message: 'Product "Wireless Headphones" is running low on stock',
          is_read: false,
          created_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 min ago
        },
        {
          id: 3,
          type: 'success',
          title: 'Payment Received',
          message: 'Payment of $299.99 has been confirmed',
          is_read: true,
          created_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), // 2 hours ago
        },
        {
          id: 4,
          type: 'info',
          title: 'System Update',
          message: 'Platform maintenance scheduled for tonight at 2 AM',
          is_read: true,
          created_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
        },
      ];
      setNotifications(mockNotifications);
      setLoading(false);
    }, 500);
  }, []);

  const getIcon = (type) => {
    switch (type) {
      case 'order':
        return <Package className="w-4 h-4 text-blue-500" />;
      case 'alert':
        return <AlertTriangle className="w-4 h-4 text-orange-500" />;
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      default:
        return <Info className="w-4 h-4 text-gray-500" />;
    }
  };

  const markAsRead = (notificationId) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === notificationId ? { ...n, is_read: true } : n))
    );
    // In a real app: POST /api/notifications/:id/read
  };

  const formatTime = (isoString) => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 max-h-96 overflow-hidden z-50">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex justify-between items-center">
        <div>
          <h3 className="font-semibold text-gray-900">Notifications</h3>
          {unreadCount > 0 && (
            <span className="text-sm text-gray-500">{unreadCount} unread</span>
          )}
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Notifications List */}
      <div className="overflow-y-auto max-h-80">
        {loading ? (
          <div className="p-8 text-center text-gray-500">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2">Loading notifications...</p>
          </div>
        ) : notifications.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <Bell className="w-12 h-12 mx-auto mb-2 text-gray-300" />
            <p>No notifications</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                  !notification.is_read ? 'bg-blue-50' : ''
                }`}
                onClick={() => !notification.is_read && markAsRead(notification.id)}
              >
                <div className="flex items-start space-x-3">
                  <div className="mt-1">{getIcon(notification.type)}</div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm text-gray-900">
                      {notification.title}
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      {notification.message}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      {formatTime(notification.created_at)}
                    </p>
                  </div>
                  {!notification.is_read && (
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {notifications.length > 0 && (
        <div className="p-3 border-t border-gray-200 text-center">
          <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
            View All Notifications
          </button>
        </div>
      )}
    </div>
  );
};

export default NotificationsDropdown;
