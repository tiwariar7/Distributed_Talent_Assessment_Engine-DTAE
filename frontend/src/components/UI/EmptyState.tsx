import React from "react";
import { Button } from "./Button";

interface EmptyStateProps {
  icon?: string;
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon = "",
  title,
  description,
  actionText,
  onAction,
}) => {
  return (
    <div
      className="glass-panel"
      style={{
        padding: "48px 24px",
        textAlign: "center",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "16px",
        width: "100%",
      }}
    >
      <span style={{ fontSize: "48px", userSelect: "none" }} role="img" aria-hidden="true">
        {icon}
      </span>
      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        <h3 style={{ fontSize: "18px", fontWeight: "bold", color: "#fff" }}>{title}</h3>
        <p style={{ color: "var(--text-muted)", fontSize: "14px", maxWidth: "400px", margin: "0 auto", lineHeight: "1.5" }}>
          {description}
        </p>
      </div>
      {actionText && onAction && (
        <Button variant="secondary" onClick={onAction}>
          {actionText}
        </Button>
      )}
    </div>
  );
};

// Refactor: Add typing hints and documentation docstrings.

// Refactor: Optimize query performance and database indexing.

// Refactor: Fix minor edge cases in calculation functions.
