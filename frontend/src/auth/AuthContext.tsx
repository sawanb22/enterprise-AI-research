import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import type { User, Session } from "@supabase/supabase-js";
import { supabase } from "./supabase";
import type { AuthContextValue, UserQuota } from "./types";
import { setAuthTokenGetter, api } from "../api";
import { SecureWorkspaceCache } from "../utils/secureStorage";

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [quota, setQuota] = useState<UserQuota | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isQuotaModalOpen, setIsQuotaModalOpen] = useState(false);

  // Provide token to API layer
  useEffect(() => {
    setAuthTokenGetter(() => session?.access_token ?? null);
  }, [session]);

  const refreshQuota = useCallback(async (): Promise<UserQuota | null> => {
    if (!session?.access_token) {
      setQuota(null);
      return null;
    }
    try {
      const q = await api.authQuota();
      setQuota(q);
      return q;
    } catch (err) {
      console.warn("Failed to fetch user quota:", err);
      return null;
    }
  }, [session]);

  // Listen to Supabase Auth state
  useEffect(() => {
    let mounted = true;

    async function initAuth() {
      try {
        const { data: { session: initialSession } } = await supabase.auth.getSession();
        if (mounted) {
          setSession(initialSession);
          setUser(initialSession?.user ?? null);
        }
      } catch (err) {
        console.error("Supabase auth session error:", err);
      } finally {
        if (mounted) setIsLoading(false);
      }
    }

    initAuth();

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, newSession) => {
        if (!mounted) return;
        setSession(newSession);
        setUser(newSession?.user ?? null);
        setIsLoading(false);
      }
    );

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, []);

  // Fetch quota when user logs in
  useEffect(() => {
    if (session?.access_token) {
      refreshQuota();
    } else {
      setQuota(null);
    }
  }, [session, refreshQuota]);

  const openAuthModal = useCallback((_mode?: "signin" | "signup") => {
    setIsAuthModalOpen(true);
  }, []);

  const closeAuthModal = useCallback(() => {
    setIsAuthModalOpen(false);
  }, []);

  const openQuotaModal = useCallback(() => {
    setIsQuotaModalOpen(true);
  }, []);

  const closeQuotaModal = useCallback(() => {
    setIsQuotaModalOpen(false);
  }, []);

  const signInWithPassword = useCallback(
    async (email: string, pass: string) => {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password: pass,
      });
      if (!error && data.session) {
        setSession(data.session);
        setUser(data.user);
        setIsAuthModalOpen(false);
      }
      return { error };
    },
    []
  );

  const signUpWithPassword = useCallback(
    async (email: string, pass: string) => {
      const { data, error } = await supabase.auth.signUp({
        email,
        password: pass,
      });
      const needsConfirmation = !data.session && !!data.user;
      if (!error && data.session) {
        setSession(data.session);
        setUser(data.user);
        setIsAuthModalOpen(false);
      }
      return { error, needsConfirmation };
    },
    []
  );

  const signOut = useCallback(async () => {
    SecureWorkspaceCache.purgeAll();
    await supabase.auth.signOut();
    setSession(null);
    setUser(null);
    setQuota(null);
  }, []);

  const value: AuthContextValue = {
    user,
    session,
    quota,
    isLoading,
    isAuthModalOpen,
    isQuotaModalOpen,
    openAuthModal,
    closeAuthModal,
    openQuotaModal,
    closeQuotaModal,
    signInWithPassword,
    signUpWithPassword,
    signOut,
    refreshQuota,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
