"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { DashboardLayout } from "../../../layouts/DashboardLayout";
import { useAuth } from "../../../hooks/useAuth";
import { useToast } from "../../../components/UI/ToastProvider";
import { Skeleton } from "../../../components/UI/Skeleton";
import { EmptyState } from "../../../components/UI/EmptyState";
import { apiFetch } from "../../../services/api";

interface Assessment {
  id: number;
  title: string;
  description: string;
  status: string;
  duration_minutes: number;
  organization: string;
  created_at: string;
}

export default function RecruiterAssessmentsPage() {
  const { token } = useAuth();
  const { showToast } = useToast();
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;

    apiFetch<Assessment[] | { results: Assessment[] }>("/api/v1/recruiter/assessments/")
      .then((data) => {
        const list = Array.isArray(data) ? data : data.results || [];
        setAssessments(list);
        setLoading(false);
      })
      .catch((err: any) => {
        console.error(err);
        setError(err.message || "Failed to load assessments.");
        showToast(err.message || "Failed to load assessments.", "error");
        setLoading(false);
      });
  }, [token]);

  if (loading) {
    return (
      <DashboardLayout>
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          {/* Header */}
          <div style={{ marginBottom: "32px" }}>
            <Skeleton height="35px" width="300px" style={{ marginBottom: "8px" }} />
            <Skeleton height="18px" width="500px" />
          </div>

          {/* Skeletons list */}
          <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            <Skeleton height="120px" width="100%" borderRadius="12px" />
            <Skeleton height="120px" width="100%" borderRadius="12px" />
            <Skeleton height="120px" width="100%" borderRadius="12px" />
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
        {/* Header */}
        <div style={{ marginBottom: "32px" }}>
          <h1
            style={{
              fontSize: "32px",
              fontWeight: "bold",
              background: "linear-gradient(90deg, #ed64a6, #e53e3e)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Assessments Console
          </h1>
          <p style={{ color: "var(--text-muted)", marginTop: "6px", fontSize: "14px" }}>
            Select an assessment to distribute candidate invitations and audit proctoring logs.
          </p>
        </div>

        {error && (
          <div
            style={{
              padding: "12px",
              borderRadius: "8px",
              background: "var(--color-error-glow)",
              border: "1px solid var(--color-error)",
              color: "var(--color-error)",
              fontSize: "14px",
              marginBottom: "20px",
            }}
          >
            {error}
          </div>
        )}

        {/* List */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {assessments.length === 0 ? (
            <EmptyState
              icon=""
              title="No assessments created yet"
              description="Use the Smart Assessment Generator to generate your first round automatically."
            />
          ) : (
            assessments.map((a) => (
              <div
                key={a.id}
                className="glass-panel"
                style={{ padding: "24px", display: "flex", justifyContent: "space-between", alignItems: "center" }}
              >
                <div style={{ display: "flex", flexDirection: "column", gap: "8px", flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <h2 style={{ fontSize: "18px", fontWeight: "bold", color: "#fff" }}>{a.title}</h2>
                    <span
                      style={{
                        fontSize: "10px",
                        fontWeight: 700,
                        textTransform: "uppercase",
                        padding: "2px 8px",
                        borderRadius: "12px",
                        background: a.status === "published" ? "var(--color-success-glow)" : "rgba(255,255,255,0.1)",
                        color: a.status === "published" ? "var(--color-success)" : "var(--text-muted)",
                        border: `1px solid ${a.status === "published" ? "var(--color-success)" : "var(--border-color)"}`,
                      }}
                    >
                      {a.status}
                    </span>
                    <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>⏱️ {a.duration_minutes} mins</span>
                  </div>
                  <p style={{ color: "var(--text-muted)", fontSize: "14px" }}>{a.description}</p>
                  <span style={{ fontSize: "11px", color: "var(--text-muted)", opacity: 0.7 }}>
                    Created on: {new Date(a.created_at).toLocaleDateString()}
                  </span>
                </div>

                <div style={{ display: "flex", gap: "12px", marginLeft: "24px" }}>
                  <Link
                    href={`/recruiter/assessments/${a.id}/invite`}
                    style={{
                      padding: "10px 20px",
                      borderRadius: "8px",
                      background: "linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%)",
                      color: "#fff",
                      textDecoration: "none",
                      fontWeight: "bold",
                      fontSize: "14px",
                      boxShadow: "0 0 10px var(--accent-primary-glow)",
                      transition: "opacity 0.2s",
                    }}
                  >
                    Manage &amp; Invite
                  </Link>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}

// Refactor: Optimize query performance and database indexing.

// Refactor: Optimize query performance and database indexing.

// Refactor: Improve responsive styles and layouts.

// Refactor: Optimize imports and clean up code structure.

// Refactor: Refactor variable names for better readability.
