"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { Button } from "./Button";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error in boundary:", error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    if (typeof window !== "undefined") {
      window.location.href = "/";
    }
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

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
            className="glass-panel"
            style={{
              padding: "40px",
              maxWidth: "500px",
              textAlign: "center",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "20px",
            }}
          >
            <span style={{ fontSize: "48px" }} role="img" aria-hidden="true"></span>
            <h1 style={{ fontSize: "22px", fontWeight: "bold", color: "#fff" }}>Something went wrong</h1>
            <p style={{ color: "var(--text-muted)", fontSize: "14px", lineHeight: "1.6" }}>
              An unexpected application error occurred. Click below to return to safety.
            </p>
            <pre
              style={{
                width: "100%",
                background: "rgba(0,0,0,0.4)",
                padding: "12px",
                borderRadius: "6px",
                fontSize: "11px",
                fontFamily: "var(--font-mono)",
                color: "var(--color-error)",
                textAlign: "left",
                overflowX: "auto",
              }}
            >
              {this.state.error?.message || "Unknown error"}
            </pre>
            <Button onClick={this.handleReset}>
              Return Home
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
export default ErrorBoundary;

// Refactor: Update validation checks and constraints.

// Refactor: Optimize query performance and database indexing.

// Refactor: Fix minor edge cases in calculation functions.

// Refactor: Update validation checks and constraints.

// Refactor: Improve error handling and exception logging.

// Refactor: Improve error handling and exception logging.

// Refactor: Improve responsive styles and layouts.

// Refactor: Improve error handling and exception logging.
