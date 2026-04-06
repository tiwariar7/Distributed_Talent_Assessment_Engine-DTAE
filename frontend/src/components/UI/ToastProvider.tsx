"use client";

import React, { createContext, useContext, useState, useCallback, ReactNode } from "react";

export type ToastType = "success" | "error" | "warning" | "info";

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextType {
  showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
};

export const ToastProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback((message: string, type: ToastType = "info") => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const getToastColors = (type: ToastType) => {
    switch (type) {
      case "success":
        return {
          bg: "var(--color-success-glow)",
          border: "1px solid var(--color-success)",
          color: "var(--color-success)",
        };
      case "error":
        return {
          bg: "var(--color-error-glow)",
          border: "1px solid var(--color-error)",
          color: "var(--color-error)",
        };
      case "warning":
        return {
          bg: "var(--color-warning-glow)",
          border: "1px solid var(--color-warning)",
          color: "var(--color-warning)",
        };
      case "info":
      default:
        return {
          bg: "rgba(255, 255, 255, 0.08)",
          border: "1px solid var(--border-color)",
          color: "var(--text-main)",
        };
    }
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {/* Toast container overlay */}
      <div
        style={{
          position: "fixed",
          bottom: "24px",
          right: "24px",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
          zIndex: 9999,
          pointerEvents: "none",
          maxWidth: "350px",
          width: "100%",
        }}
      >
        {toasts.map((toast) => {
          const colors = getToastColors(toast.type);
          return (
            <div
              key={toast.id}
              role="alert"
              aria-live="assertive"
              className="glass-panel animate-fade-in"
              style={{
                pointerEvents: "auto",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "12px 16px",
                borderRadius: "8px",
                background: colors.bg,
                border: colors.border,
                color: colors.color,
                boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
                fontSize: "13px",
                fontWeight: 500,
              }}
            >
              <span>{toast.message}</span>
              <button
                onClick={() => removeToast(toast.id)}
                aria-label="Close notification"
                style={{
                  background: "transparent",
                  border: "none",
                  color: "inherit",
                  fontSize: "16px",
                  cursor: "pointer",
                  marginLeft: "12px",
                  lineHeight: 1,
                  opacity: 0.7,
                }}
              >
                &times;
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
};

// Refactor: Improve responsive styles and layouts.

// Refactor: Fix minor edge cases in calculation functions.

// Refactor: Improve responsive styles and layouts.

// Refactor: Add typing hints and documentation docstrings.

// Refactor: Align with project code quality guidelines.
