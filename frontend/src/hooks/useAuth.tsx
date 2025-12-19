import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, Profile } from '../types';
import { authApi, profileApi } from '../api/client';

interface AuthContextType {
  user: User | null;
  profile: Profile | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = async () => {
    try {
      const userData = await authApi.getMe();
      setUser(userData);
    } catch {
      setUser(null);
      authApi.logout();
    }
  };

  const refreshProfile = async () => {
    try {
      const profileData = await profileApi.getMyProfile();
      setProfile(profileData);
    } catch {
      setProfile(null);
    }
  };

  useEffect(() => {
    const init = async () => {
      if (authApi.isAuthenticated()) {
        await refreshUser();
        await refreshProfile();
      }
      setLoading(false);
    };
    init();
  }, []);

  const login = async (email: string, password: string) => {
    await authApi.login(email, password);
    await refreshUser();
    await refreshProfile();
  };

  const register = async (email: string, password: string) => {
    await authApi.register(email, password);
    await refreshUser();
  };

  const logout = () => {
    authApi.logout();
    setUser(null);
    setProfile(null);
  };

  return (
    <AuthContext.Provider
      value={{ user, profile, loading, login, register, logout, refreshUser, refreshProfile }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
