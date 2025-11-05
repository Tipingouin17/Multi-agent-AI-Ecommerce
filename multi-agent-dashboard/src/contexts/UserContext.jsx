
import { createContext, useContext, useState, useEffect } from 'react';

const UserContext = createContext();

export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // In a real app, you'd fetch this from an API
    // For now, we'll use a mock user
    const mockUser = {
      id: 1,
      name: 'Sophie Laurent',
      email: 'sophie.laurent@example.com',
      role: 'admin',
    };
    setUser(mockUser);
    setLoading(false);
  }, []);

  const logout = () => {
    setUser(null);
    // In a real app, you'd also call a logout API endpoint
    // and likely redirect to a login page.
  };

  return (
    <UserContext.Provider value={{ user, loading, logout }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};
