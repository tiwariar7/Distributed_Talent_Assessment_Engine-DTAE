"use client";

import React from "react";
import Link from "next/link";

interface AuthLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({
  children,
  title,
  subtitle,
}) => {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        padding: "20px",
        background: "var(--bg-main)",
        position: "relative",
      }}
    >
      <div
        className="glass-panel animate-fade-in"
        style={{
          maxWidth: "420px",
          width: "100%",
          padding: "36px",
          display: "flex",
          flexDirection: "column",
          gap: "24px",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <Link href="/" style={{ textDecoration: "none", display: "inline-block", marginBottom: "8px" }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--accent-primary)", display: "block", margin: "0 auto" }}><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" fill="currentColor"/></svg>
          </Link>
          <h1 style={{ fontSize: "24px", fontWeight: 800, color: "#fff", letterSpacing: "-0.5px" }}>
            {title}
          </h1>
          {subtitle && (
            <p style={{ color: "var(--text-muted)", fontSize: "14px", marginTop: "6px" }}>
              {subtitle}
            </p>
          )}
        </div>
        {children}
      </div>
    </div>
  );
};

// Refactor: Improve responsive styles and layouts.

// Refactor: Optimize imports and clean up code structure.
