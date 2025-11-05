import { User, Settings, LogOut, HelpCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../../contexts/UserContext';

const UserProfileDropdown = ({ onClose }) => {
  const navigate = useNavigate();
  const { user, logout } = useUser();

  const handleLogout = () => {
    logout();
    onClose();
    navigate('/');
  };

  const handleNavigation = (path) => {
    navigate(path);
    onClose();
  };

  if (!user) return null;

  return (
    <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
      {/* User Info Header */}
      <div className="p-4 border-b border-gray-200">
        <p className="font-semibold text-gray-900">{user.name}</p>
        <p className="text-sm text-gray-500">{user.email}</p>
        <p className="text-xs text-gray-400 mt-1 capitalize">{user.role}</p>
      </div>

      {/* Menu Items */}
      <div className="py-2">
        <button
          onClick={() => handleNavigation('/profile')}
          className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center text-gray-700"
        >
          <User className="inline w-4 h-4 mr-3" />
          My Profile
        </button>
        <button
          onClick={() => handleNavigation('/settings')}
          className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center text-gray-700"
        >
          <Settings className="inline w-4 h-4 mr-3" />
          Settings
        </button>
        <button
          onClick={() => handleNavigation('/help')}
          className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center text-gray-700"
        >
          <HelpCircle className="inline w-4 h-4 mr-3" />
          Help & Support
        </button>
      </div>

      {/* Logout */}
      <div className="border-t border-gray-200">
        <button
          onClick={handleLogout}
          className="w-full px-4 py-3 text-left hover:bg-red-50 flex items-center text-red-600 font-medium"
        >
          <LogOut className="inline w-4 h-4 mr-3" />
          Logout
        </button>
      </div>
    </div>
  );
};

export default UserProfileDropdown;
