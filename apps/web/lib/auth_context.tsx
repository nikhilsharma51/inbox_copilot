
'use client';

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from 'react';

import { User, APIError } from '@/lib/types';
import { api } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  authError: string | null;

  login: () => void;
  logout: () => Promise<void>;
  disconnect: () => Promise<void>;
  getUser: () => Promise<User | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);

  const getUser = useCallback(async (): Promise<User | null> => {
    try {
      const currentUser = await api.auth.me();

      setUser(currentUser);
      setAuthError(null);

      return currentUser;
    } catch (error) {
      if (error instanceof APIError && error.status === 401) {
        setUser(null);
        setAuthError(null);

        return null;
      }

      const message =
        error instanceof Error
          ? error.message
          : 'Unable to verify session';

      setAuthError(message);
      throw error;
    }
  }, []);

  const login = useCallback(() => {
    window.location.assign(api.auth.getLoginUrl());
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.auth.logout();

      setUser(null);
      setAuthError(null);
    } catch (error) {
      setAuthError(
        error instanceof Error ? error.message : 'Logout failed'
      );

      throw error;
    }
  }, []);

  const disconnect = useCallback(async () => {
    await api.auth.disconnect();
    await getUser();
  }, [getUser]);

  useEffect(() => {
    let active = true;

    const initializeAuth = async () => {
      try {
        await getUser();
      } catch {
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    };

    initializeAuth();

    return () => {
      active = false;
    };
  }, [getUser]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        authError,
        login,
        logout,
        disconnect,
        getUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}
