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
