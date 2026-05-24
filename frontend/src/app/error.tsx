"use client";

import React, { useEffect } from "react";
import { Button } from "../components/UI/Button";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Global Next.js App error caught:", error);
  }, [error]);

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
          <span style={{ fontSize: "64px", fontWeight: 800, color: "var(--color-error)", userSelect: "none" }}>!</span>
        </span>
        <h1 style={{ fontSize: "26px", fontWeight: 800, color: "#fff", letterSpacing: "-1px" }}>
          Application Error
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "14px", lineHeight: "1.6" }}>
          A critical rendering error occurred in the platform. Try reloading or return home.
        </p>
        {error.message && (
          <pre
            style={{
              width: "100%",
              background: "rgba(0,0,0,0.3)",
              padding: "10px",
              borderRadius: "6px",
              fontSize: "11px",
              fontFamily: "var(--font-mono)",
              color: "var(--color-error)",
              textAlign: "left",
              overflowX: "auto",
            }}
          >
            {error.message}
          </pre>
        )}
        <div style={{ display: "flex", gap: "10px" }}>
          <Button onClick={reset} variant="secondary">
            Retry Page
          </Button>
          <Button onClick={() => (window.location.href = "/")}>
            Go Home
          </Button>
        </div>
      </div>
    </div>
  );
}
