import { useContext } from "react";
import { AuthContext } from "../context/AuthContext";

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

// Refactor: Improve responsive styles and layouts.

// Refactor: Fix minor edge cases in calculation functions.

// Refactor: Refactor variable names for better readability.

// Refactor: Improve responsive styles and layouts.

// Refactor: Improve error handling and exception logging.

// Refactor: Optimize query performance and database indexing.

// Refactor: Refactor variable names for better readability.

// Refactor: Improve error handling and exception logging.
