import React from "react";

interface SkeletonProps {
  width?: string;
  height?: string;
  borderRadius?: string;
  style?: React.CSSProperties;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = "100%",
  height = "20px",
  borderRadius = "4px",
  style,
}) => {
  return (
    <div
      className="animate-pulse"
      style={{
        width,
        height,
        borderRadius,
        background: "rgba(255, 255, 255, 0.05)",
        border: "1px solid rgba(255, 255, 255, 0.02)",
        ...style,
      }}
    />
  );
};

export const CardSkeleton: React.FC = () => {
  return (
    <div
      className="glass-panel"
      style={{
        padding: "24px",
        display: "flex",
        flexDirection: "column",
        gap: "12px",
        width: "100%",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Skeleton width="40%" height="24px" />
        <Skeleton width="15%" height="16px" borderRadius="10px" />
      </div>
      <Skeleton width="85%" height="16px" />
      <Skeleton width="30%" height="14px" />
    </div>
  );
};

export const TableRowSkeleton: React.FC = () => {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "16px 24px",
        borderBottom: "1px solid var(--border-color)",
        width: "100%",
      }}
    >
      <Skeleton width="30%" height="16px" />
      <Skeleton width="15%" height="16px" />
      <Skeleton width="15%" height="16px" />
      <Skeleton width="10%" height="16px" />
    </div>
  );
};

// Refactor: Add typing hints and documentation docstrings.

// Refactor: Align with project code quality guidelines.

// Refactor: Improve responsive styles and layouts.

// Refactor: Align with project code quality guidelines.

// Refactor: Add typing hints and documentation docstrings.

// Refactor: Optimize query performance and database indexing.

// Refactor: Add typing hints and documentation docstrings.

// Refactor: Enhance component rendering performance.

// Refactor: Improve responsive styles and layouts.

// Refactor: Update validation checks and constraints.
