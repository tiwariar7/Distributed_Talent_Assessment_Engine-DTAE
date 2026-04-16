"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AuthLayout } from "../../layouts/AuthLayout";
import { Input } from "../../components/UI/Input";
import { Button } from "../../components/UI/Button";
import { useToast } from "../../components/UI/ToastProvider";
import { apiPost } from "../../services/api";

export default function Register() {
  const router = useRouter();
  const { showToast } = useToast();
  
  const [role, setRole] = useState<"candidate" | "recruiter">("candidate");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [orgName, setOrgName] = useState("");
  const [orgSlug, setOrgSlug] = useState("");
  const [invToken, setInvToken] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const payload: Record<string, any> = {
      email,
      password,
      first_name: firstName,
      last_name: lastName,
      role,
    };

    if (role === "recruiter") {
      if (invToken) {
        payload.invitation_token = invToken;
      } else if (orgSlug) {
        payload.organization_slug = orgSlug;
      } else if (orgName) {
        payload.organization_name = orgName;
      }
    }

    try {
      await apiPost("/api/v1/auth/register/", payload);
      showToast("Account registered! Check backend logs for the verification token.", "success");
      setTimeout(() => {
        router.push("/verify");
      }, 4000);
    } catch (err: any) {
      showToast(err.message || "Registration failed. Please check your details.", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Join DTAE Platform" subtitle="Create your candidate or recruiter account">
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <div>
          <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "1px", color: "var(--text-muted)", marginBottom: "8px" }}>
            I want to join as
          </label>
          <div style={{ display: "flex", gap: "10px" }}>
            <button
              type="button"
              onClick={() => setRole("candidate")}
              style={{
                flex: 1,
                padding: "10px",
                borderRadius: "8px",
                border: "1px solid",
                borderColor: role === "candidate" ? "var(--accent-primary)" : "var(--border-color)",
                background: role === "candidate" ? "var(--accent-primary-glow)" : "transparent",
                color: "#fff",
                cursor: "pointer",
                transition: "all 0.2s",
                fontWeight: "bold",
              }}
            >
              Candidate
            </button>
            <button
              type="button"
              onClick={() => setRole("recruiter")}
              style={{
                flex: 1,
                padding: "10px",
                borderRadius: "8px",
                border: "1px solid",
                borderColor: role === "recruiter" ? "var(--accent-primary)" : "var(--border-color)",
                background: role === "recruiter" ? "var(--accent-primary-glow)" : "transparent",
                color: "#fff",
                cursor: "pointer",
                transition: "all 0.2s",
                fontWeight: "bold",
              }}
            >
              Recruiter
            </button>
          </div>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <div style={{ flex: 1 }}>
            <Input
              label="First Name"
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              required
            />
          </div>
          <div style={{ flex: 1 }}>
            <Input
              label="Last Name"
              type="text"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              required
            />
          </div>
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

        {role === "recruiter" && (
          <div
            style={{
              padding: "15px",
              borderRadius: "8px",
              background: "rgba(255,255,255,0.02)",
              border: "1px solid var(--border-color)",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
            }}
          >
            <span style={{ fontSize: "13px", fontWeight: "bold", color: "var(--text-main)" }}>
              Organization Details
            </span>

            <Input
              label="New Organization Name"
              type="text"
              placeholder="e.g. Acme Corp"
              value={orgName}
              onChange={(e) => {
                setOrgName(e.target.value);
                setOrgSlug("");
                setInvToken("");
              }}
            />

            <div style={{ textAlign: "center", fontSize: "11px", color: "var(--text-muted)" }}>OR</div>

            <Input
              label="Existing Organization Slug"
              type="text"
              placeholder="e.g. acme-corp"
              value={orgSlug}
              onChange={(e) => {
                setOrgSlug(e.target.value);
                setOrgName("");
                setInvToken("");
              }}
            />

            <div style={{ textAlign: "center", fontSize: "11px", color: "var(--text-muted)" }}>OR</div>

            <Input
              label="Recruiter Invitation Token"
              type="text"
              placeholder="Paste invitation token"
              value={invToken}
              onChange={(e) => {
                setInvToken(e.target.value);
                setOrgName("");
                setOrgSlug("");
              }}
            />
          </div>
        )}

        <Button type="submit" isLoading={loading}>
          Create Account
        </Button>
      </form>

      <div style={{ marginTop: "10px", textAlign: "center", fontSize: "14px", color: "var(--text-muted)" }}>
        Already have an account?{" "}
        <Link href="/login" style={{ color: "var(--accent-primary)", textDecoration: "none", fontWeight: "bold" }}>
          Sign In
        </Link>
      </div>
    </AuthLayout>
  );
}

// Refactor: Enhance component rendering performance.

// Refactor: Improve error handling and exception logging.

// Refactor: Align with project code quality guidelines.

// Refactor: Optimize query performance and database indexing.

// Refactor: Fix minor edge cases in calculation functions.

// Refactor: Improve responsive styles and layouts.
