import React, { createContext, useState, useContext, useEffect } from 'react';

// Create AuthContext
const AuthContext = createContext(null);

// Custom hook to use the auth context
export const useAuth = () => {
  return useContext(AuthContext);
};

// Auth Provider component
export const AuthProvider = ({ children }) => {
  // For development, we'll always be authenticated
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  const [user, setUser] = useState({ username: 'developer' });

  // Mock login function
  const login = async (username, password) => {
    // For demo purposes, accept any username/password
    console.log('Mock login with:', username);
    setUser({ username });
    setIsAuthenticated(true);
    return true;
  };

  // Mock logout function
  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
  };

  // Value provided to consumers of this context
  const value = {
    isAuthenticated,
    user,
    login,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext; 