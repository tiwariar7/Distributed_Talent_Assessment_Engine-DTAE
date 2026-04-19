"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "../hooks/useAuth";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, loading, isAuthenticated } = useAuth();

  // Route guarding redirection (UX layer)
  React.useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push("/login");
    }
  }, [loading, isAuthenticated, router]);

  if (loading || !isAuthenticated) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
        <div className="animate-spin" style={{ width: "40px", height: "40px", border: "3px solid var(--border-color)", borderTopColor: "var(--accent-primary)", borderRadius: "50%" }} />
      </div>
    );
  }

  const isRecruiter = user?.isRecruiter;
  
  const navItems = isRecruiter
    ? [
        { label: "Manage Assessments", href: "/recruiter/assessments" },
        { label: "Recruiter Dash", href: "/recruiter" },
        { label: "DSA Prep Dashboard", href: "/dsa-intelligence" },
        { label: "Profile Settings", href: "/profile" },
      ]
    : [
        { label: "Dashboard", href: "/candidate/dashboard" },
        { label: "My Invitations", href: "/candidate/invitations" },
        { label: "DSA Preparation", href: "/dsa-intelligence" },
        { label: "Profile Settings", href: "/profile" },
      ];

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      {/* Dynamic Header */}
      <header
        className="glass-panel"
        style={{
          borderRadius: "0",
          borderBottom: "1px solid var(--border-color)",
          padding: "12px 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          position: "sticky",
          top: 0,
          zIndex: 100,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--accent-primary)", display: "inline-block", verticalAlign: "middle" }}><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" fill="currentColor"/></svg>
          <span style={{ fontWeight: 800, fontSize: "16px", letterSpacing: "0.5px" }}>DTAE Platform</span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          {/* User Display Name */}
          <span style={{ fontSize: "13px", color: "var(--text-main)", fontWeight: 500 }}>
            {user?.name}
          </span>
          {/* Role Badge */}
          <span
            style={{
              fontSize: "10px",
              fontWeight: 700,
              padding: "3px 10px",
              borderRadius: "20px",
              background: isRecruiter
                ? "linear-gradient(135deg, hsla(340, 82%, 60%, 0.15), hsla(0, 78%, 55%, 0.15))"
                : "linear-gradient(135deg, hsla(263, 90%, 65%, 0.15), hsla(217, 91%, 60%, 0.15))",
              border: `1px solid ${isRecruiter ? "hsla(340, 82%, 60%, 0.3)" : "hsla(263, 90%, 65%, 0.3)"}`,
              color: isRecruiter ? "hsl(340, 82%, 75%)" : "hsl(263, 90%, 80%)",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
            }}
          >
            {isRecruiter ? "Recruiter" : "Candidate"}
          </span>

          <button
            onClick={logout}
            style={{
              background: "transparent",
              border: "1px solid var(--color-error)",
              borderRadius: "6px",
              padding: "6px 12px",
              fontSize: "12px",
              fontWeight: "bold",
              color: "var(--color-error)",
              cursor: "pointer",
              transition: "all 0.2s",
            }}
            onMouseOver={(e) => {
              (e.currentTarget as HTMLElement).style.background = "var(--color-error-glow)";
            }}
            onMouseOut={(e) => {
              (e.currentTarget as HTMLElement).style.background = "transparent";
            }}
          >
            Logout
          </button>
        </div>
      </header>

      {/* Main Panel Content */}
      <div style={{ display: "flex", flex: 1, position: "relative" }}>
        {/* Sidebar Nav */}
        <nav
          className="glass-panel"
          style={{
            width: "250px",
            borderRadius: "0",
            borderRight: "1px solid var(--border-color)",
            padding: "24px 16px",
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            minHeight: "calc(100vh - 61px)",
            position: "sticky",
            top: "61px",
            left: 0,
          }}
        >
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                style={{
                  display: "flex",
                  alignItems: "center",
                  padding: "10px 14px",
                  borderRadius: "8px",
                  textDecoration: "none",
                  fontSize: "14px",
                  fontWeight: isActive ? "bold" : 500,
                  color: isActive ? "#fff" : "var(--text-muted)",
                  background: isActive ? "rgba(255, 255, 255, 0.08)" : "transparent",
                  border: `1px solid ${isActive ? "var(--border-color)" : "transparent"}`,
                  transition: "all 0.2s",
                }}
                onMouseOver={(e) => {
                  if (!isActive) {
                    (e.currentTarget as HTMLElement).style.color = "#fff";
                    (e.currentTarget as HTMLElement).style.background = "rgba(255, 255, 255, 0.03)";
                  }
                }}
                onMouseOut={(e) => {
                  if (!isActive) {
                    (e.currentTarget as HTMLElement).style.color = "var(--text-muted)";
                    (e.currentTarget as HTMLElement).style.background = "transparent";
                  }
                }}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Content Pane */}
        <main style={{ flex: 1, padding: "32px", overflowY: "auto" }}>
          {children}
        </main>
      </div>
    </div>
  );
};

// Refactor: Optimize imports and clean up code structure.

// Refactor: Improve responsive styles and layouts.

// Refactor: Optimize imports and clean up code structure.

// Refactor: Update validation checks and constraints.

// Refactor: Optimize query performance and database indexing.

// Refactor: Align with project code quality guidelines.
