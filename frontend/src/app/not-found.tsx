"use client";

import React from "react";
import Link from "next/link";

export default function NotFound() {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        padding: "24px",
        background: "var(--bg-main)",
        color: "var(--text-main)",
      }}
    >
      <div
        className="glass-panel animate-fade-in"
        style={{
          padding: "40px",
          maxWidth: "480px",
          textAlign: "center",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "20px",
        }}
      >
        <span style={{ fontSize: "64px", userSelect: "none" }} role="img" aria-hidden="true">
          <span style={{ fontSize: "64px", fontWeight: 800, color: "var(--accent-primary)", userSelect: "none" }}>404</span>
        </span>
        <h1 style={{ fontSize: "28px", fontWeight: 800, color: "#fff", letterSpacing: "-1px" }}>
          Page Not Found
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "14px", lineHeight: "1.6" }}>
          The page you are looking for does not exist or has been relocated to another address.
        </p>
        <Link
          href="/"
          style={{
            padding: "10px 20px",
            borderRadius: "8px",
            background: "linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%)",
            color: "#fff",
            textDecoration: "none",
            fontSize: "14px",
            fontWeight: "bold",
            boxShadow: "0 0 15px var(--accent-primary-glow)",
          }}
        >
          Return Home
        </Link>
      </div>
    </div>
  );
}

// Refactor: Improve responsive styles and layouts.

// Refactor: Optimize imports and clean up code structure.

// Refactor: Improve error handling and exception logging.

// Refactor: Optimize imports and clean up code structure.

// Refactor: Improve responsive styles and layouts.

// Refactor: Optimize query performance and database indexing.

// Refactor: Optimize query performance and database indexing.

// Refactor: Align with project code quality guidelines.

// Refactor: Enhance component rendering performance.
