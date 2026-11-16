
'use client';

import {
    createContext,
    useContext,
    useState,
    useEffect,
    useCallback,
    ReactNode,
} from 'react';

import { User } from '../types/api-types';
import { api } from './api';

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    authError: string | null;
    login: () => void;
    logout: () => Promise<void>;
    getUser: () => Promise<User | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
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
            if (
                typeof error === 'object' &&
                error !== null &&
                'status' in error &&
                error.status === 401
            ) {
                setUser(null);
                return null;
            }

            throw error;
        }
    }, []);

    const login = useCallback(() => {
        window.location.href = api.auth.getLoginUrl();
    }, []);

    const logout = useCallback(async () => {
        try {
            await api.auth.logout();
        } finally {
            setUser(null);
        }
    }, []);

    useEffect(() => {
        let active = true;

        const initializeAuth = async () => {
            try {
                await getUser();
            } catch (error) {
                if (active) {
                    setAuthError(
                        error instanceof Error
                            ? error.message
                            : 'Unable to verify session'
                    );
                }
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
            value= {{
        user,
            isAuthenticated: !!user,
                isLoading,
                authError,
                login,
                logout,
                getUser,
            }
}
        >
    { children }
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
