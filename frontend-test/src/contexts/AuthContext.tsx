import React, { createContext, useContext, useState, useEffect } from 'react';
import * as api from '../services/api';

interface User {
  id: number;
  email: string;
  name: string;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const storedUser = localStorage.getItem('user');
    console.log('Initial user from localStorage:', storedUser);
    return storedUser ? JSON.parse(storedUser) : null;
  });

  const login = async (email: string, password: string) => {
    try {
      const response = await api.login(email, password);
      console.log('Login response:', response);

      if (!response.token || !response.user) {
        console.log(' Login response missing token or user:', response);
        throw new Error('Invalid login response');
      }

      // Store token
      api.setAuthToken(response.token);
      
      // Store user data
      setUser(response.user);
      localStorage.setItem('user', JSON.stringify(response.user));
      
    } catch (error) {
      console.log(' Login error:', error);
      throw error;
    }
  };

  const logout = () => {
    api.clearAuthToken();
    localStorage.removeItem('user');
    setUser(null);
  };

  const value = {
    user,
    login,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
