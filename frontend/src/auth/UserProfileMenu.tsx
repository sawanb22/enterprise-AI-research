import React, { useState, useRef, useEffect } from "react";
import { useAuth } from "./AuthContext";

export function UserProfileMenu() {
  const { user, signOut, openAuthModal, quota } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (!user) {
    return (
      <div className="user-profile-menu-container">
        <button
          type="button"
          className="celestial-signin-btn"
          onClick={() => openAuthModal("signin")}
        >
          <span className="btn-starlight-sparkle">✦</span>
          <span>Sign In / Join</span>
        </button>
      </div>
    );
  }

  const initial = (user.email ? user.email[0] : "U").toUpperCase();
  const remaining = quota?.remaining_runs ?? 5;
  const maxRuns = quota?.max_free_runs ?? 5;

  return (
    <div className="user-profile-menu-container" ref={menuRef}>
      <button
        type="button"
        className={`celestial-user-pill ${isOpen ? "active" : ""}`}
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <div className="celestial-avatar-orb">
          <span>{initial}</span>
        </div>
        <div className="celestial-user-info">
          <span className="celestial-user-email">{user.email}</span>
          <span className="celestial-user-sub">
            {remaining}/{maxRuns} Credits
          </span>
        </div>
        <span className="celestial-chevron">▾</span>
      </button>

      {isOpen && (
        <div className="celestial-user-dropdown">
          <div className="dropdown-header">
            <span className="dropdown-user-email">{user.email}</span>
            <span className="dropdown-user-role">Research Account</span>
          </div>

          <div className="dropdown-quota-summary">
            <div className="dropdown-quota-header">
              <span>Research Allowance</span>
              <span className="quota-pill-count">{remaining} / {maxRuns} Inquiries</span>
            </div>
            <div className="dropdown-quota-bar">
              <div
                className="dropdown-quota-fill"
                style={{ width: `${((maxRuns - remaining) / maxRuns) * 100}%` }}
              />
            </div>
          </div>

          <div className="dropdown-divider" />

          <button
            type="button"
            className="dropdown-logout-btn"
            onClick={async () => {
              setIsOpen(false);
              await signOut();
            }}
          >
            <span>Sign Out</span>
          </button>
        </div>
      )}
    </div>
  );
}
