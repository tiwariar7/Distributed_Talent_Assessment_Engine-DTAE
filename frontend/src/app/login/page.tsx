"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "../../hooks/useAuth";
import { AuthLayout } from "../../layouts/AuthLayout";
import { Input } from "../../components/UI/Input";
import { Button } from "../../components/UI/Button";
import { useToast } from "../../components/UI/ToastProvider";
import Link from "next/link";

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, isAuthenticated, user, loading } = useAuth();
  const { showToast } = useToast();

  const [email, setEmail] = useState("candidate@demo.test");
  const [password, setPassword] = useState("DemoPass123!");
  const [activeTab, setActiveTab] = useState<"candidate" | "recruiter">("candidate");

  // Sync tab with search parameters on load
  useEffect(() => {
    const roleParam = searchParams.get("role");
    if (roleParam === "recruiter") {
      setActiveTab("recruiter");
      setEmail("recruiter@demo.test");
    } else if (roleParam === "candidate") {
      setActiveTab("candidate");
      setEmail("candidate@demo.test");
    }
  }, [searchParams]);

  // Handle redirect if logged in
  useEffect(() => {
    if (isAuthenticated && user) {
      if (user.isRecruiter) {
        router.push("/recruiter/assessments");
      } else {
        router.push("/candidate/dashboard");
      }
    }
  }, [isAuthenticated, user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const profile = await login(email, password);
      showToast(`Welcome back, ${profile.name}!`, "success");
    } catch (err: any) {
      showToast(err.message || "Authentication failed. Please verify credentials.", "error");
    }
  };

  const fillCredentials = (role: "candidate" | "recruiter") => {
    setActiveTab(role);
    if (role === "candidate") {
      setEmail("candidate@demo.test");
      setPassword("DemoPass123!");
    } else {
      setEmail("recruiter@demo.test");
      setPassword("DemoPass123!");
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {/* Tabs */}
      <div
        style={{
          display: "flex",
          background: "rgba(0, 0, 0, 0.2)",
          padding: "4px",
          borderRadius: "8px",
          border: "1px solid var(--border-color)",
        }}
      >
        <button
          type="button"
          onClick={() => fillCredentials("candidate")}
          style={{
            flex: 1,
            padding: "8px",
            borderRadius: "6px",
            background: activeTab === "candidate" ? "rgba(255,255,255,0.08)" : "transparent",
            border: "none",
            color: activeTab === "candidate" ? "#fff" : "var(--text-muted)",
            fontSize: "13px",
            fontWeight: "bold",
            cursor: "pointer",
          }}
        >
          Candidate
        </button>
        <button
          type="button"
          onClick={() => fillCredentials("recruiter")}
          style={{
            flex: 1,
            padding: "8px",
            borderRadius: "6px",
            background: activeTab === "recruiter" ? "rgba(255,255,255,0.08)" : "transparent",
            border: "none",
            color: activeTab === "recruiter" ? "#fff" : "var(--text-muted)",
            fontSize: "13px",
            fontWeight: "bold",
            cursor: "pointer",
          }}
        >
          Recruiter
        </button>
      </div>

      <Input
        label="Email Address"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />

      <Input
        label="Password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />

      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px", marginTop: "4px" }}>
        <Link href="/register" style={{ color: "var(--accent-primary)", textDecoration: "none", fontWeight: "bold" }}>
          Create Account
        </Link>
        <Link href="/forgot-password" style={{ color: "var(--text-muted)", textDecoration: "none" }}>
          Forgot Password?
        </Link>
      </div>

      <Button type="submit" isLoading={loading} style={{ marginTop: "8px" }}>
        Sign In
      </Button>

      {/* Demo Credentials */}
      <div style={{ marginTop: "16px", borderTop: "1px solid var(--border-color)", paddingTop: "16px" }}>
        <div style={{ fontSize: "11px", fontWeight: "bold", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "8px", textAlign: "center" }}>
          Demo Credentials
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
          <button
            type="button"
            onClick={() => fillCredentials("candidate")}
            style={{
              flex: 1,
              padding: "10px",
              borderRadius: "8px",
              background: "rgba(255, 255, 255, 0.03)",
              border: "1px solid var(--border-color)",
              cursor: "pointer",
              color: "var(--text-main)",
              fontSize: "12px",
              textAlign: "left",
              display: "flex",
              flexDirection: "column",
              gap: "2px",
            }}
          >
            <span style={{ fontWeight: "bold", color: "hsl(263, 90%, 80%)" }}>Candidate</span>
            <span style={{ fontSize: "10px", color: "var(--text-muted)" }}>candidate@demo.test</span>
          </button>
          <button
            type="button"
            onClick={() => fillCredentials("recruiter")}
            style={{
              flex: 1,
              padding: "10px",
              borderRadius: "8px",
              background: "rgba(255, 255, 255, 0.03)",
              border: "1px solid var(--border-color)",
              cursor: "pointer",
              color: "var(--text-main)",
              fontSize: "12px",
              textAlign: "left",
              display: "flex",
              flexDirection: "column",
              gap: "2px",
            }}
          >
            <span style={{ fontWeight: "bold", color: "hsl(340, 82%, 75%)" }}>Recruiter</span>
            <span style={{ fontSize: "10px", color: "var(--text-muted)" }}>recruiter@demo.test</span>
          </button>
        </div>
      </div>
    </form>
  );
}

export default function LoginPage() {
  return (
    <AuthLayout title="DTAE Sign In" subtitle="Distributed Talent Assessment Engine">
      <Suspense fallback={
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "40px" }}>
          <div className="animate-spin" style={{ width: "24px", height: "24px", border: "2px solid var(--border-color)", borderTopColor: "var(--accent-primary)", borderRadius: "50%" }} />
        </div>
      }>
        <LoginContent />
      </Suspense>
    </AuthLayout>
  );
}

// Refactor: Align with project code quality guidelines.

// Refactor: Refactor variable names for better readability.

// Refactor: Refactor variable names for better readability.

// Refactor: Update validation checks and constraints.

// Refactor: Align with project code quality guidelines.

// Refactor: Refactor variable names for better readability.
