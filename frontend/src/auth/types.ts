import type { User, Session } from "@supabase/supabase-js";

export interface UserQuota {
  user_id: string;
  total_runs_used: number;
  max_free_runs: number;
  remaining_runs: number;
  is_quota_exhausted: boolean;
}

export interface UserProfileResponse {
  user: {
    id: string;
    email: string;
    full_name: string | null;
    avatar_url: string | null;
    role: string;
  };
  quota: UserQuota;
}

export interface AuthContextValue {
  user: User | null;
  session: Session | null;
  quota: UserQuota | null;
  isLoading: boolean;
  isAuthModalOpen: boolean;
  isQuotaModalOpen: boolean;
  openAuthModal: (mode?: "signin" | "signup") => void;
  closeAuthModal: () => void;
  openQuotaModal: () => void;
  closeQuotaModal: () => void;
  signInWithPassword: (email: string, password: string) => Promise<{ error: Error | null }>;
  signUpWithPassword: (email: string, password: string) => Promise<{ error: Error | null; needsConfirmation?: boolean }>;
  signOut: () => Promise<void>;
  refreshQuota: () => Promise<UserQuota | null>;
}
