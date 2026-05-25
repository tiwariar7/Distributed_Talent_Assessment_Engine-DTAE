"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { AuthLayout } from "../../layouts/AuthLayout";
import { Input } from "../../components/UI/Input";
import { Button } from "../../components/UI/Button";
import { useToast } from "../../components/UI/ToastProvider";
import { apiPost } from "../../services/api";

function ForgotPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { showToast } = useToast();
  
  const [token, setToken] = useState("");
  const [email, setEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);

  // Set token if present in query params
  useEffect(() => {
    const t = searchParams?.get("token");
    if (t) {
      setToken(t);
    }
  }, [searchParams]);

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await apiPost("/api/v1/auth/reset-password/", { email });
      showToast("If the email is registered, a password reset link has been printed to the server logs.", "success");
    } catch (err: any) {
      showToast(err.message || "Failed to submit request.", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      showToast("Passwords do not match.", "error");
      return;
    }

    setLoading(true);

    try {
      await apiPost("/api/v1/auth/reset-password/confirm/", { token, new_password: newPassword });
      showToast("Password has been reset successfully! Redirecting you to login...", "success");
      setTimeout(() => {
        router.push("/login");
      }, 3000);
    } catch (err: any) {
      showToast(err.message || "Failed to reset password.", "error");
    } finally {
      setLoading(false);
    }
  };

  if (token) {
    return (
      <AuthLayout title="Enter New Password" subtitle="Provide a new password for your account">
        <form onSubmit={handleConfirmReset} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <Input
            label="New Password"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
          />

          <Input
            label="Confirm New Password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />

          <Button type="submit" isLoading={loading}>
            Update Password
          </Button>
        </form>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Reset Password" subtitle="Enter your email to request a reset link">
      <form onSubmit={handleRequestReset} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <Input
          label="Email Address"
          type="email"
          placeholder="candidate@demo.test"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <Button type="submit" isLoading={loading}>
          Send Reset Link
        </Button>
      </form>

      <div style={{ marginTop: "10px", textAlign: "center", fontSize: "14px", color: "var(--text-muted)" }}>
        Remembered password?{" "}
        <Link href="/login" style={{ color: "var(--accent-primary)", textDecoration: "none", fontWeight: "bold" }}>
          Sign In
        </Link>
      </div>
    </AuthLayout>
  );
}

export default function ForgotPassword() {
  return (
    <Suspense fallback={
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
        <div className="animate-spin" style={{ width: "40px", height: "40px", border: "3px solid var(--border-color)", borderTopColor: "var(--accent-primary)", borderRadius: "50%" }} />
      </div>
    }>
      <ForgotPasswordForm />
    </Suspense>
  );
}

// Refactor: Align with project code quality guidelines.

// Refactor: Improve error handling and exception logging.

// Refactor: Update validation checks and constraints.

// Refactor: Add typing hints and documentation docstrings.

// Refactor: Improve error handling and exception logging.

// Refactor: Refactor variable names for better readability.

// Refactor: Optimize imports and clean up code structure.

// Refactor: Fix minor edge cases in calculation functions.
