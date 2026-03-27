"use client";

import React from "react";
import { AuthProvider } from "../context/AuthContext";
import { ToastProvider } from "../components/UI/ToastProvider";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <ToastProvider>
        {children}
      </ToastProvider>
    </AuthProvider>
  );
}

// Refactor: Update validation checks and constraints.

// Refactor: Enhance component rendering performance.

// Refactor: Fix minor edge cases in calculation functions.

// Refactor: Update validation checks and constraints.

// Refactor: Update validation checks and constraints.

// Refactor: Optimize query performance and database indexing.

// Refactor: Update validation checks and constraints.
