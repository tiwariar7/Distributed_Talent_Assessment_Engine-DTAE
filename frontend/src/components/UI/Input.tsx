import React from "react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  id,
  style,
  ...props
}) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "6px", width: "100%" }}>
      {label && (
        <label
          htmlFor={inputId}
          style={{
            fontSize: "13px",
            fontWeight: 500,
            color: error ? "var(--color-error)" : "var(--text-muted)",
          }}
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        aria-invalid={!!error}
        aria-describedby={error ? `${inputId}-error` : undefined}
        style={{
          width: "100%",
          padding: "12px",
          borderRadius: "8px",
          border: `1px solid ${error ? "var(--color-error)" : "var(--border-color)"}`,
          background: "rgba(0, 0, 0, 0.3)",
          color: "var(--text-main)",
          fontSize: "14px",
          transition: "border-color 0.2s, box-shadow 0.2s",
          outline: "none",
          ...style,
        }}
        {...props}
      />
      {error && (
        <span
          id={`${inputId}-error`}
          role="alert"
          style={{
            fontSize: "12px",
            color: "var(--color-error)",
            marginTop: "2px",
          }}
        >
          {error}
        </span>
      )}
    </div>
  );
};

// Refactor: Fix minor edge cases in calculation functions.

// Refactor: Fix minor edge cases in calculation functions.
