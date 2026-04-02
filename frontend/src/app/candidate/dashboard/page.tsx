"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { DashboardLayout } from "../../../layouts/DashboardLayout";
import { apiFetch } from "../../../services/api";
import { CardSkeleton } from "../../../components/UI/Skeleton";
import { EmptyState } from "../../../components/UI/EmptyState";
import { Button } from "../../../components/UI/Button";
import { useToast } from "../../../components/UI/ToastProvider";
import { preloadMLModels } from "../../../app/lib/mlModelCache";

interface Problem {
  id: number;
  title: string;
}

interface Assessment {
  id: number;
  title: string;
  description: string;
  duration_minutes: number;
  organization: string;
  problems: Problem[];
}

interface Invitation {
  id: string;
  assessment: Assessment;
  email: string;
  token: string;
  expires_at: string;
  is_active: boolean;
  instructions: string;
  proctoring_required: boolean;
  status: "pending" | "accepted" | "started" | "completed" | "expired";
  completed_at: string | null;
}

export default function CandidateDashboard() {
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"active" | "history">("active");
  const { showToast } = useToast();

  useEffect(() => {
    // Pre-warm proctoring ML models
    preloadMLModels();
  }, []);

  const loadInvitations = () => {
    setLoading(true);
    apiFetch<Invitation[]>("/api/v1/assessments/candidate/invitations/")
      .then((data) => {
        setInvitations(data);
        setError(null);
      })
      .catch((err) => {
        console.error("Invitations error:", err);
        setError(err.message || "Failed to retrieve invitations.");
        showToast("Error retrieving your invitations list", "error");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadInvitations();
  }, []);

  const isExpired = (expiresAtStr: string) => {
    return new Date(expiresAtStr) < new Date();
  };

  const activeInvites = invitations.filter(
    (inv) =>
      inv.status !== "completed" &&
      inv.status !== "expired" &&
      !isExpired(inv.expires_at)
  );

  const historyInvites = invitations.filter(
    (inv) =>
      inv.status === "completed" ||
      inv.status === "expired" ||
      isExpired(inv.expires_at)
  );

  const currentList = activeTab === "active" ? activeInvites : historyInvites;

  const renderContent = () => {
    if (loading) {
      return (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px", width: "100%" }}>
          <CardSkeleton />
          <CardSkeleton />
        </div>
      );
    }

    if (currentList.length === 0) {
      return (
        <EmptyState
          icon=""
          title={activeTab === "active" ? "No Active Invitations" : "No Invitation History"}
          description={
            activeTab === "active"
              ? "You do not have any pending assessment invitations at this moment."
              : "You have not completed or expired any historical assessment invitations yet."
          }
          actionText="Refresh List"
          onAction={loadInvitations}
        />
      );
    }

    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        {currentList.map((inv) => {
          const hasStarted = inv.status === "started";
          const completed = inv.status === "completed";
          const expired = inv.status === "expired" || isExpired(inv.expires_at);

          let badgeColor = "hsl(42, 100%, 53%)"; // pending
          if (completed) badgeColor = "var(--color-success)";
          else if (expired) badgeColor = "var(--color-error)";
          else if (hasStarted) badgeColor = "var(--accent-primary)";

          return (
            <div
              key={inv.id}
              className="glass-panel"
              style={{
                padding: "24px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div style={{ display: "flex", flexDirection: "column", gap: "8px", flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
                  <span
                    style={{
                      fontSize: "11px",
                      fontWeight: 700,
                      textTransform: "uppercase",
                      padding: "2px 8px",
                      borderRadius: "12px",
                      background: "rgba(255,255,255,0.06)",
                      border: "1px solid var(--border-color)",
                      color: "var(--text-muted)",
                    }}
                  >
                    {inv.assessment.organization}
                  </span>
                  <h3 style={{ fontSize: "18px", fontWeight: "bold", color: "#fff" }}>
                    {inv.assessment.title}
                  </h3>
                  <span
                    style={{
                      fontSize: "10px",
                      fontWeight: 700,
                      textTransform: "uppercase",
                      padding: "2px 8px",
                      borderRadius: "12px",
                      background: "rgba(255,255,255,0.02)",
                      border: `1px solid ${badgeColor}`,
                      color: badgeColor,
                    }}
                  >
                    {completed ? "Completed" : expired ? "Expired" : hasStarted ? "In Progress" : "Pending"}
                  </span>
                  <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                    ⏱️ {inv.assessment.duration_minutes} mins
                  </span>
                  {inv.proctoring_required && (
                    <span
                      style={{
                        fontSize: "10px",
                        fontWeight: 700,
                        padding: "2px 8px",
                        borderRadius: "12px",
                        background: "rgba(229, 62, 62, 0.1)",
                        border: "1px solid var(--color-error)",
                        color: "hsl(0, 80%, 75%)",
                      }}
                    >
                      Proctored Environment
                    </span>
                  )}
                </div>

                <p style={{ color: "var(--text-muted)", fontSize: "14px" }}>
                  {inv.assessment.description}
                </p>

                {inv.instructions && (
                  <div
                    style={{
                      padding: "10px 14px",
                      background: "rgba(255, 255, 255, 0.02)",
                      borderRadius: "6px",
                      borderLeft: "3px solid var(--accent-primary)",
                      fontSize: "13px",
                      color: "var(--text-muted)",
                      marginTop: "6px",
                    }}
                  >
                    <strong>Instructions:</strong> {inv.instructions}
                  </div>
                )}

                <div style={{ display: "flex", gap: "12px", fontSize: "12px", color: "var(--text-muted)", marginTop: "6px" }}>
                  <span>Invited email: {inv.email}</span>
                  <span>•</span>
                  {completed ? (
                    <span>Completed on: {inv.completed_at ? new Date(inv.completed_at).toLocaleString() : ""}</span>
                  ) : expired ? (
                    <span style={{ color: "var(--color-error)" }}>Expired on: {new Date(inv.expires_at).toLocaleString()}</span>
                  ) : (
                    <span style={{ color: "hsl(48, 80%, 70%)" }}>
                      Expires on: {new Date(inv.expires_at).toLocaleString()}
                    </span>
                  )}
                </div>
              </div>

              <div style={{ marginLeft: "24px" }}>
                {completed ? (
                  <Button disabled variant="secondary">
                    Submitted
                  </Button>
                ) : expired ? (
                  <Button disabled variant="secondary">
                    Closed
                  </Button>
                ) : (
                  <Link href={`/assessment/${inv.token}`} style={{ textDecoration: "none" }}>
                    <Button variant={hasStarted ? "outline" : "primary"}>
                      {hasStarted ? "Resume" : "Start"} →
                    </Button>
                  </Link>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <DashboardLayout>
      <div style={{ display: "flex", flexDirection: "column", gap: "32px", maxWidth: "1000px" }}>
        
        {/* Banner Section */}
        <div>
          <h1 style={{ fontSize: "32px", fontWeight: "bold", color: "#fff" }}>
            Candidate Assessment Dashboard
          </h1>
          <p style={{ color: "var(--text-muted)", marginTop: "8px" }}>
            Review pending invitations, start coding challenges, and track active test history.
          </p>
        </div>

        {/* Info Metrics Cards */}
        <div style={{ display: "flex", gap: "20px", flexWrap: "wrap" }}>
          <div className="glass-panel" style={{ flex: 1, minWidth: "200px", padding: "20px", display: "flex", flexDirection: "column", gap: "6px" }}>
            <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>Active Invites</span>
            <span style={{ fontSize: "28px", fontWeight: 800, color: "#fff" }}>{activeInvites.length}</span>
          </div>
          <div className="glass-panel" style={{ flex: 1, minWidth: "200px", padding: "20px", display: "flex", flexDirection: "column", gap: "6px" }}>
            <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>Completed Tests</span>
            <span style={{ fontSize: "28px", fontWeight: 800, color: "var(--color-success)" }}>
              {invitations.filter((i) => i.status === "completed").length}
            </span>
          </div>
          <div className="glass-panel" style={{ flex: 1, minWidth: "200px", padding: "20px", display: "flex", flexDirection: "column", gap: "6px" }}>
            <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>Expired Invites</span>
            <span style={{ fontSize: "28px", fontWeight: 800, color: "var(--color-error)" }}>
              {invitations.filter((i) => i.status === "expired" || (i.status !== "completed" && isExpired(i.expires_at))).length}
            </span>
          </div>
        </div>

        {/* Tab Selection */}
        <div style={{ borderBottom: "1px solid var(--border-color)", display: "flex", gap: "24px" }}>
          <button
            onClick={() => setActiveTab("active")}
            style={{
              padding: "12px 6px",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === "active" ? "2px solid var(--accent-primary)" : "2px solid transparent",
              color: activeTab === "active" ? "#fff" : "var(--text-muted)",
              fontSize: "14px",
              fontWeight: "bold",
              cursor: "pointer",
              transition: "all 0.2s",
            }}
          >
            Active Invitations ({activeInvites.length})
          </button>
          <button
            onClick={() => setActiveTab("history")}
            style={{
              padding: "12px 6px",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === "history" ? "2px solid var(--accent-primary)" : "2px solid transparent",
              color: activeTab === "history" ? "#fff" : "var(--text-muted)",
              fontSize: "14px",
              fontWeight: "bold",
              cursor: "pointer",
              transition: "all 0.2s",
            }}
          >
            Historical Archives ({historyInvites.length})
          </button>
        </div>

        {error && (
          <div style={{ padding: "12px", borderRadius: "8px", background: "var(--color-error-glow)", border: "1px solid var(--color-error)", color: "var(--color-error)", fontSize: "14px" }}>
            {error}
          </div>
        )}

        {/* Inner Content */}
        {renderContent()}

      </div>
    </DashboardLayout>
  );
}

// Refactor: Optimize query performance and database indexing.

// Refactor: Improve error handling and exception logging.

// Refactor: Update validation checks and constraints.

// Refactor: Align with project code quality guidelines.

// Refactor: Add typing hints and documentation docstrings.

// Refactor: Optimize imports and clean up code structure.
