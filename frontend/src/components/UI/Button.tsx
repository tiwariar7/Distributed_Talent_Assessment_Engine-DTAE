import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "danger";
  isLoading?: boolean;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = "primary",
  isLoading = false,
  icon,
  className = "",
  disabled,
  ...props
}) => {
  const getStyles = () => {
    const base = {
      padding: "10px 20px",
      borderRadius: "8px",
      fontWeight: "bold",
      fontSize: "14px",
      cursor: "pointer",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      gap: "8px",
      transition: "all 0.2s ease-in-out",
      border: "none",
      outline: "none",
      color: "#fff",
      boxShadow: "none",
    };

    if (disabled || isLoading) {
      return {
        ...base,
        opacity: 0.5,
        cursor: "not-allowed",
        background: "rgba(255, 255, 255, 0.08)",
        border: "1px solid var(--border-color)",
        color: "var(--text-muted)",
      };
    }

    switch (variant) {
      case "secondary":
        return {
          ...base,
          background: "rgba(255, 255, 255, 0.06)",
          border: "1px solid var(--border-color)",
          color: "var(--text-main)",
        };
      case "outline":
        return {
          ...base,
          background: "transparent",
          border: "1px solid var(--accent-primary)",
          color: "var(--accent-primary)",
        };
      case "danger":
        return {
          ...base,
          background: "linear-gradient(135deg, var(--color-error) 0%, hsl(358, 83%, 45%) 100%)",
          boxShadow: "0 0 10px rgba(255, 75, 75, 0.2)",
        };
      case "primary":
      default:
        return {
          ...base,
          background: "linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%)",
          boxShadow: "0 0 15px var(--accent-primary-glow)",
        };
    }
  };

  return (
    <button
      disabled={disabled || isLoading}
      style={getStyles() as React.CSSProperties}
      aria-busy={isLoading}
      {...props}
    >
      {isLoading ? (
        <span
          className="animate-spin"
          style={{
            width: "16px",
            height: "16px",
            border: "2px solid rgba(255,255,255,0.3)",
            borderTopColor: "#fff",
            borderRadius: "50%",
          }}
        />
      ) : (
        icon
      )}
      {children}
    </button>
  );
};

// Refactor: Add typing hints and documentation docstrings.
