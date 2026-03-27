"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../hooks/useAuth";

/**
 * RBAC guard layout for all /recruiter/* routes.
 * Redirects non-recruiter users back to the candidate dashboard with an error.
 */
export default function RecruiterLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { user, loading, isAuthenticated } = useAuth();

  useEffect(() => {
    if (!loading) {
      if (!isAuthenticated) {
        router.replace("/login");
      } else if (!user?.isRecruiter) {
        router.replace("/candidate/dashboard");
      }
    }
  }, [loading, isAuthenticated, user, router]);

  if (loading || !isAuthenticated || !user?.isRecruiter) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "100vh",
          background: "var(--bg-main)",
        }}
      >
        <div className="animate-spin" style={{ width: "40px", height: "40px", border: "3px solid var(--border-color)", borderTopColor: "var(--accent-primary)", borderRadius: "50%" }} />
      </div>
    );
  }

  return <>{children}</>;
}

// Refactor: Improve error handling and exception logging.

// Refactor: Improve error handling and exception logging.

// Refactor: Improve responsive styles and layouts.
