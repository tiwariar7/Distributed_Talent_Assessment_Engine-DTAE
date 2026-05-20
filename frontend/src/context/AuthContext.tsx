"use client";

import React, { createContext, useState, useEffect, useCallback, ReactNode } from "react";
import { decodeToken, isRecruiter, isCandidate, getUserDisplayName, DecodedToken } from "../services/auth";
import { registerTokenGetter, registerLogoutHandler, apiPost } from "../services/api";

interface UserProfile {
  id: number;
  email: string;
  name: string;
  isRecruiter: boolean;
  isCandidate: boolean;
}

interface AuthContextType {
  token: string | null;
  user: UserProfile | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<UserProfile>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Helper to get/set refresh token via secure client cookie
const getRefreshCookie = (): string | null => {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/dtae_refresh=([^;]+)/);
  return match ? decodeURIComponent(csrfEscape(match[1])) : null;
};

const setRefreshCookie = (token: string | null) => {
  if (typeof document === "undefined") return;
  if (token) {
    document.cookie = `dtae_refresh=${encodeURIComponent(token)}; path=/; max-age=604800; SameSite=Strict; Secure`;
  } else {
    document.cookie = "dtae_refresh=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
  }
};

// Escapes potential injection characters
function csrfEscape(str: string): string {
  return str.replace(/[<>&'"]/g, "");
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  // Set up stateless API bindings to retrieve token from React state
  const getAccessToken = useCallback(() => token, [token]);

  const logout = useCallback(() => {
    setTokenState(null);
    setUser(null);
    setRefreshCookie(null);
    if (typeof window !== "undefined") {
      // Clear token references on logout
      window.dispatchEvent(new Event("auth_logout"));
    }
  }, []);

  useEffect(() => {
    registerTokenGetter(getAccessToken);
  }, [getAccessToken]);

  useEffect(() => {
    registerLogoutHandler(logout);
  }, [logout]);

  const handleDecodedToken = useCallback((accessToken: string) => {
    const decoded = decodeToken(accessToken);
    if (!decoded) {
      logout();
      return null;
    }

    const profile: UserProfile = {
      id: decoded.user_id,
      email: decoded.email,
      name: getUserDisplayName(accessToken),
      isRecruiter: isRecruiter(accessToken),
      isCandidate: isCandidate(accessToken),
    };

    setTokenState(accessToken);
    setUser(profile);
    return decoded;
  }, [logout]);

  const refreshToken = useCallback(async () => {
    const refresh = getRefreshCookie();
    if (!refresh) {
      logout();
      setLoading(false);
      return;
    }

    try {
      // Refresh JWT token from simplejwt endpoint
      const data = await apiPost<{ access: string }>(
        "/api/v1/auth/refresh/",
        { refresh }
      );
      handleDecodedToken(data.access);
    } catch (err) {
      console.error("Token refresh failed:", err);
      logout();
    } finally {
      setLoading(false);
    }
  }, [handleDecodedToken, logout]);

  // Bootstrapping session on mount
  useEffect(() => {
    refreshToken();
  }, []);

  // Automatic token refresh scheduler
  useEffect(() => {
    if (!token) return;

    const decoded = decodeToken(token);
    if (!decoded) return;

    // Refresh 30 seconds before expiration
    const expiryTime = decoded.exp * 1000 - Date.now();
    const delay = Math.max(0, expiryTime - 30000);

    const timer = setTimeout(() => {
      refreshToken();
    }, delay);

    return () => clearTimeout(timer);
  }, [token, refreshToken]);

  const login = async (email: string, password: string): Promise<UserProfile> => {
    setLoading(true);
    try {
      const data = await apiPost<{ access: string; refresh: string }>(
        "/api/v1/auth/login/",
        { email, password }
      );

      setRefreshCookie(data.refresh);
      const profile = {
        id: decodeToken(data.access)?.user_id || 0,
        email,
        name: getUserDisplayName(data.access),
        isRecruiter: isRecruiter(data.access),
        isCandidate: isCandidate(data.access),
      };

      setTokenState(data.access);
      setUser(profile);
      return profile;
    } catch (err: any) {
      logout();
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        isAuthenticated: !!token,
        loading,
        login,
        logout,
        refreshToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// Refactor: Refactor variable names for better readability.

// Refactor: Improve error handling and exception logging.

// Refactor: Add typing hints and documentation docstrings.

// Refactor: Refactor variable names for better readability.

// Refactor: Improve responsive styles and layouts.

// Refactor: Enhance component rendering performance.
