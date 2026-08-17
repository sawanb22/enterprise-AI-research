import React, { useState, useEffect } from "react";
import { useAuth } from "./AuthContext";

export function AuthModal() {
  const { isAuthModalOpen, closeAuthModal, signInWithPassword, signUpWithPassword } = useAuth();
  const [tab, setTab] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isAuthModalOpen) {
      setErrorMessage(null);
      setInfoMessage(null);
    }
  }, [isAuthModalOpen, tab]);

  // Handle ESC key
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && isAuthModalOpen) {
        closeAuthModal();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isAuthModalOpen, closeAuthModal]);

  if (!isAuthModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setInfoMessage(null);

    if (!email.trim() || !password.trim()) {
      setErrorMessage("Please fill in both email and password.");
      return;
    }

    if (password.length < 6) {
      setErrorMessage("Password must be at least 6 characters long.");
      return;
    }

    setIsSubmitting(true);
    try {
      if (tab === "signin") {
        const { error } = await signInWithPassword(email.trim(), password);
        if (error) {
          setErrorMessage(error.message || "Failed to sign in. Please verify your credentials.");
        }
      } else {
        const { error, needsConfirmation } = await signUpWithPassword(email.trim(), password);
        if (error) {
          setErrorMessage(error.message || "Failed to register account.");
        } else if (needsConfirmation) {
          setInfoMessage("Account created! Check your email to confirm your account.");
        }
      }
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "An unexpected error occurred.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="celestial-modal-overlay" onClick={closeAuthModal}>
      <div
        className="celestial-auth-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-modal-title"
      >
        <button
          type="button"
          className="celestial-modal-close"
          onClick={closeAuthModal}
          aria-label="Close dialog"
        >
          ✕
        </button>

        <div className="celestial-modal-header">
          <div className="celestial-modal-icon">✦</div>
          <h2 id="auth-modal-title" className="celestial-modal-title">
            {tab === "signin" ? "Enter the Cosmos" : "Join the Expedition"}
          </h2>
          <p className="celestial-modal-subtitle">
            {tab === "signin"
              ? "Sign in to access your private research projects and 5 free stars."
              : "Create an account to get 5 Lifetime Free Research Inquiries."}
          </p>
        </div>

        <div className="celestial-auth-tabs">
          <button
            type="button"
            className={`celestial-tab-btn ${tab === "signin" ? "active" : ""}`}
            onClick={() => setTab("signin")}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`celestial-tab-btn ${tab === "signup" ? "active" : ""}`}
            onClick={() => setTab("signup")}
          >
            Create Account
          </button>
        </div>

        {errorMessage && (
          <div className="celestial-auth-alert error">
            <span>⚠️</span>
            <span>{errorMessage}</span>
          </div>
        )}

        {infoMessage && (
          <div className="celestial-auth-alert info">
            <span>✨</span>
            <span>{infoMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="celestial-auth-form">
          <div className="form-group">
            <label htmlFor="auth-email">Email Address</label>
            <input
              id="auth-email"
              type="email"
              placeholder="explorer@cosmos.ai"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isSubmitting}
              autoFocus
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="auth-password">Password</label>
            <input
              id="auth-password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isSubmitting}
              required
            />
          </div>

          <button
            type="submit"
            className="celestial-auth-submit-btn"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <span className="btn-spinner" />
            ) : (
              <span>{tab === "signin" ? "Sign In" : "Create Account & Claim 5 Stars"}</span>
            )}
          </button>
        </form>

        <div className="celestial-modal-footer">
          <small>
            ⚡ Pilot Project: Free 5 lifetime messages granted per registered explorer.
          </small>
        </div>
      </div>
    </div>
  );
}
