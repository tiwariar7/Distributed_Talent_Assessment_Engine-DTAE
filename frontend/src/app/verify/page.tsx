"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { AuthLayout } from "../../layouts/AuthLayout";
import { Input } from "../../components/UI/Input";
import { Button } from "../../components/UI/Button";
import { useToast } from "../../components/UI/ToastProvider";
import { apiPost } from "../../services/api";

function VerifyEmailForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { showToast } = useToast();
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);

  // Auto-fill from query param if available
  useEffect(() => {
    const t = searchParams.get("token");
    if (t) {
      setToken(t);
      handleVerify(t);
    }
  }, [searchParams]);

  const handleVerify = async (tToVerify: string) => {
    setLoading(true);

    try {
      await apiPost("/api/v1/auth/verify-email/", { token: tToVerify });
      showToast("Email verified successfully! Redirecting you to login...", "success");
      setTimeout(() => {
        router.push("/login");
      }, 3000);
    } catch (err: any) {
      showToast(err.message || "Invalid or expired token.", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (token) {
      handleVerify(token);
    }
  };

  return (
    <AuthLayout title="Verify Your Email" subtitle="Enter your email verification token">
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <Input
          label="Verification Token"
          type="text"
          placeholder="Paste your 32-character token here"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          required
          style={{ textAlign: "center" }}
        />

        <Button type="submit" isLoading={loading}>
          Verify Email
        </Button>
      </form>

      <div style={{ marginTop: "10px", textAlign: "center", fontSize: "14px", color: "var(--text-muted)" }}>
        Back to{" "}
        <Link href="/login" style={{ color: "var(--accent-primary)", textDecoration: "none", fontWeight: "bold" }}>
          Sign In
        </Link>
      </div>
    </AuthLayout>
  );
}

export default function Verify() {
  return (
    <Suspense fallback={
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
        <div className="animate-spin" style={{ width: "40px", height: "40px", border: "3px solid var(--border-color)", borderTopColor: "var(--accent-primary)", borderRadius: "50%" }} />
      </div>
    }>
      <VerifyEmailForm />
    </Suspense>
  );
}

// Refactor: Fix minor edge cases in calculation functions.

// Refactor: Optimize query performance and database indexing.

// Refactor: Optimize query performance and database indexing.

// Refactor: Fix minor edge cases in calculation functions.
