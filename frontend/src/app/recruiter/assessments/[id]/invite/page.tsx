"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import { DashboardLayout } from "../../../../../layouts/DashboardLayout";
import { useAuth } from "../../../../../hooks/useAuth";
import { useToast } from "../../../../../components/UI/ToastProvider";
import { Input } from "../../../../../components/UI/Input";
import { Button } from "../../../../../components/UI/Button";
import { apiFetch, apiPost } from "../../../../../services/api";

interface Invitation {
  id: string;
  email: string;
  token: string;
  expires_at: string;
  instructions: string;
  proctoring_required: boolean;
  invitation_message: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  is_active: boolean;
  violation_count: number;
  proctoring_status: string;
}

interface Assessment {
  id: number;
  title: string;
  description: string;
  duration_minutes: number;
}

export default function InviteCandidatesDashboard() {
  const params = useParams();
  const assessmentId = params.id as string;
  const { token } = useAuth();
  const { showToast } = useToast();

  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);

  // Form State
  const [emailsText, setEmailsText] = useState("");
  const [deadline, setDeadline] = useState("");
  const [instructions, setInstructions] = useState(
    "Please ensure your camera and microphone are connected. Sharing your entire screen is required."
  );
  const [proctoringRequired, setProctoringRequired] = useState(true);
  const [invitationMessage, setInvitationMessage] = useState(
    "You are invited to complete this technical assessment."
  );
  const [submitting, setSubmitting] = useState(false);

  // Set default deadline to 7 days from now
  useEffect(() => {
    const nextWeek = new Date();
    nextWeek.setDate(nextWeek.getDate() + 7);
    const yyyy = nextWeek.getFullYear();
    const mm = String(nextWeek.getMonth() + 1).padStart(2, "0");
    const dd = String(nextWeek.getDate()).padStart(2, "0");
    setDeadline(`${yyyy}-${mm}-${dd}T12:00`);
  }, []);

  const loadData = useCallback(() => {
    if (!token) return;

    // Fetch assessment details
    apiFetch<Assessment>(`/api/v1/recruiter/assessments/${assessmentId}/`)
      .then((data) => setAssessment(data))
      .catch((err: any) => {
        console.error(err);
        showToast("Assessment not found.", "error");
      });

    // Fetch invitations list
    apiFetch<Invitation[] | { results: Invitation[] }>(`/api/v1/recruiter/assessments/${assessmentId}/invitations/`)
      .then((data) => {
        const list = Array.isArray(data) ? data : data.results || [];
        setInvitations(list);
        setLoading(false);
      })
      .catch((err: any) => {
        console.error(err);
        showToast("Failed to load invitations.", "error");
        setLoading(false);
      });
  }, [assessmentId, token]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handle invitation creation
  const handleInviteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    const emailList = emailsText
      .split(/[\n,]+/)
      .map((email) => email.trim())
      .filter((email) => email.length > 0);

    if (emailList.length === 0) {
      showToast("Please enter at least one email address.", "error");
      setSubmitting(false);
      return;
    }

    const payload = {
      emails: emailList,
      deadline: new Date(deadline).toISOString(),
      instructions,
      proctoring_required: proctoringRequired,
      invitation_message: invitationMessage,
    };

    try {
      const data = await apiPost<{ invitations: any[] }>(
        `/api/v1/recruiter/assessments/${assessmentId}/invite/`,
        payload
      );

      showToast(
        `Successfully generated ${data.invitations.length} invitation(s). Links printed to Django server logs.`,
        "success"
      );
      setEmailsText("");
      loadData();
    } catch (err: any) {
      showToast(err.message || "An error occurred while creating invitations.", "error");
    } finally {
      setSubmitting(false);
    }
  };

  // Revoke active invitation
  const handleRevoke = async (invitationId: string) => {
    const confirmRevoke = confirm("Are you sure you want to revoke this invitation?");
    if (!confirmRevoke) return;

    try {
      await apiPost(`/api/v1/recruiter/invitations/${invitationId}/revoke/`, {});
      showToast("Invitation revoked successfully.", "success");
      loadData();
    } catch (err: any) {
      showToast(err.message || "Failed to revoke invitation.", "error");
    }
  };

  // Copy invitation link to clipboard
  const handleCopyLink = (invToken: string) => {
    const appUrl =
      typeof window !== "undefined"
        ? `${window.location.protocol}//${window.location.host}`
        : "http://localhost:3000";
    const inviteUrl = `${appUrl}/assessment/${invToken}`;
    navigator.clipboard.writeText(inviteUrl);
    showToast("Invitation URL copied to clipboard!", "success");
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div style={{ display: "flex", alignItems: "center", justifyItems: "center", minHeight: "50vh" }}>
          <div className="animate-spin" style={{ width: "40px", height: "40px", border: "3px solid var(--border-color)", borderTopColor: "var(--accent-primary)", borderRadius: "50%", margin: "0 auto" }} />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
        {/* Header */}
        <div style={{ marginBottom: "32px" }}>
          <span style={{ fontSize: "12px", textTransform: "uppercase", color: "var(--accent-primary)", fontWeight: "bold" }}>
            Hiring Assessment
          </span>
          <h1 style={{ fontSize: "28px", fontWeight: "bold", color: "#fff", marginTop: "4px", marginBlockEnd: "8px" }}>
            {assessment?.title}
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "14px" }}>
            Configure rules, invite candidates, and monitor real-time anti-cheating logs.
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "24px", marginBottom: "32px" }}>
          {/* Invitation Form Card */}
          <div className="glass-panel" style={{ padding: "24px" }}>
            <h2 style={{ fontSize: "18px", fontWeight: "bold", marginBottom: "16px", color: "var(--text-main)" }}>
              Invite Candidates
            </h2>

            <form onSubmit={handleInviteSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div>
                <label style={{ display: "block", fontSize: "13px", color: "var(--text-muted)", marginBottom: "6px" }}>
                  Candidate Emails (comma or newline separated)
                </label>
                <textarea
                  rows={3}
                  placeholder="candidate1@test.com, candidate2@test.com"
                  value={emailsText}
                  onChange={(e) => setEmailsText(e.target.value)}
                  required
                  style={{
                    width: "100%",
                    padding: "12px",
                    borderRadius: "8px",
                    border: "1px solid var(--border-color)",
                    background: "rgba(0,0,0,0.3)",
                    color: "var(--text-main)",
                    outline: "none",
                    resize: "vertical",
                    fontSize: "14px",
                  }}
                />
              </div>

              <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", alignItems: "flex-end" }}>
                <div style={{ flex: 1, minWidth: "180px" }}>
                  <label style={{ display: "block", fontSize: "13px", color: "var(--text-muted)", marginBottom: "6px" }}>
                    Deadline Time Limit
                  </label>
                  <input
                    type="datetime-local"
                    value={deadline}
                    onChange={(e) => setDeadline(e.target.value)}
                    required
                    style={{
                      width: "100%",
                      padding: "10px",
                      borderRadius: "8px",
                      border: "1px solid var(--border-color)",
                      background: "rgba(0,0,0,0.3)",
                      color: "var(--text-main)",
                      outline: "none",
                      fontSize: "13px",
                    }}
                  />
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "10px", padding: "10px 0" }}>
                  <input
                    type="checkbox"
                    id="proctoring"
                    checked={proctoringRequired}
                    onChange={(e) => setProctoringRequired(e.target.checked)}
                    style={{ cursor: "pointer", width: "16px", height: "16px" }}
                  />
                  <label
                    htmlFor="proctoring"
                    style={{ fontSize: "13px", color: "var(--text-muted)", cursor: "pointer", userSelect: "none" }}
                  >
                    Require Proctoring
                  </label>
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "13px", color: "var(--text-muted)", marginBottom: "6px" }}>
                  Candidate Instructions
                </label>
                <textarea
                  rows={2}
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px",
                    borderRadius: "8px",
                    border: "1px solid var(--border-color)",
                    background: "rgba(0,0,0,0.3)",
                    color: "var(--text-main)",
                    outline: "none",
                    fontSize: "14px",
                  }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "13px", color: "var(--text-muted)", marginBottom: "6px" }}>
                  Invitation Message (Optional)
                </label>
                <textarea
                  rows={2}
                  value={invitationMessage}
                  onChange={(e) => setInvitationMessage(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px",
                    borderRadius: "8px",
                    border: "1px solid var(--border-color)",
                    background: "rgba(0,0,0,0.3)",
                    color: "var(--text-main)",
                    outline: "none",
                    fontSize: "14px",
                  }}
                />
              </div>

              <Button type="submit" isLoading={submitting}>
                Create Invitations
              </Button>
            </form>
          </div>

          {/* Info panel */}
          <div
            className="glass-panel"
            style={{ padding: "24px", height: "fit-content", display: "flex", flexDirection: "column", gap: "16px" }}
          >
            <h2 style={{ fontSize: "18px", fontWeight: "bold", color: "var(--text-main)" }}>
              Proctoring &amp; Audit Console
            </h2>
            <p style={{ color: "var(--text-muted)", fontSize: "14px", lineHeight: "1.6" }}>
              The system logs violations in real-time. When a candidate exceeds 2 warnings, their session is marked as{" "}
              <strong>auto-submitted</strong>, and the exam is terminated immediately.
            </p>
            <div
              style={{
                background: "rgba(255,255,255,0.02)",
                border: "1px solid var(--border-color)",
                borderRadius: "8px",
                padding: "16px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "8px 0",
                  borderBottom: "1px solid rgba(255,255,255,0.05)",
                }}
              >
                <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>Total Invitations:</span>
                <span style={{ fontSize: "13px", fontWeight: "bold" }}>{invitations.length}</span>
              </div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "8px 0",
                  borderBottom: "1px solid rgba(255,255,255,0.05)",
                }}
              >
                <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>Active Candidates:</span>
                <span style={{ fontSize: "13px", fontWeight: "bold", color: "var(--color-success)" }}>
                  {invitations.filter((i) => i.status === "started").length}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0" }}>
                <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>Completed:</span>
                <span style={{ fontSize: "13px", fontWeight: "bold", color: "var(--accent-secondary)" }}>
                  {invitations.filter((i) => i.status === "completed").length}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Invitations Table List */}
        <div className="glass-panel" style={{ padding: "24px", overflowX: "auto" }}>
          <h2 style={{ fontSize: "18px", fontWeight: "bold", marginBottom: "16px", color: "var(--text-main)" }}>
            Active Invitations &amp; Logs
          </h2>

          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "13px" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border-color)", color: "var(--text-muted)" }}>
                <th style={{ padding: "12px 8px" }}>Email</th>
                <th style={{ padding: "12px 8px" }}>Status</th>
                <th style={{ padding: "12px 8px" }}>Proctored</th>
                <th style={{ padding: "12px 8px" }}>Telemetry Warnings</th>
                <th style={{ padding: "12px 8px" }}>Session Status</th>
                <th style={{ padding: "12px 8px" }}>Expiry</th>
                <th style={{ padding: "12px 8px" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {invitations.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    style={{ textAlign: "center", padding: "24px", color: "var(--text-muted)", opacity: 0.5 }}
                  >
                    No candidate invitations created yet.
                  </td>
                </tr>
              ) : (
                invitations.map((i) => (
                  <tr key={i.id} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.05)" }}>
                    <td style={{ padding: "14px 8px", fontWeight: "bold" }}>{i.email}</td>
                    <td style={{ padding: "14px 8px" }}>
                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: 700,
                          textTransform: "uppercase",
                          padding: "2px 8px",
                          borderRadius: "12px",
                          background:
                            i.status === "completed"
                              ? "var(--color-success-glow)"
                              : i.status === "started"
                              ? "var(--accent-primary-glow)"
                              : "rgba(255,255,255,0.05)",
                          color:
                            i.status === "completed"
                              ? "var(--color-success)"
                              : i.status === "started"
                              ? "var(--accent-primary)"
                              : "var(--text-muted)",
                        }}
                      >
                        {i.status}
                      </span>
                    </td>
                    <td style={{ padding: "14px 8px" }}>{i.proctoring_required ? "Yes" : "No"}</td>
                    <td style={{ padding: "14px 8px" }}>
                      {i.violation_count > 0 ? (
                        <span style={{ color: "var(--color-error)", fontWeight: "bold" }}>
                          {i.violation_count} warnings
                        </span>
                      ) : (
                        <span style={{ color: "var(--color-success)" }}>0 warnings</span>
                      )}
                    </td>
                    <td style={{ padding: "14px 8px", textTransform: "capitalize" }}>
                      <span
                        style={{
                          color:
                            i.proctoring_status === "auto_submitted" || i.proctoring_status === "suspended"
                              ? "var(--color-error)"
                              : i.proctoring_status === "warned"
                              ? "var(--color-warning)"
                              : i.proctoring_status === "active"
                              ? "var(--color-success)"
                              : "inherit",
                        }}
                      >
                        {i.proctoring_status}
                      </span>
                    </td>
                    <td style={{ padding: "14px 8px" }}>{new Date(i.expires_at).toLocaleDateString()}</td>
                    <td style={{ padding: "14px 8px", display: "flex", gap: "8px" }}>
                      <button
                        onClick={() => handleCopyLink(i.token)}
                        style={{
                          padding: "4px 8px",
                          borderRadius: "4px",
                          border: "1px solid var(--border-color)",
                          background: "rgba(255,255,255,0.05)",
                          color: "var(--text-main)",
                          cursor: "pointer",
                          fontSize: "11px",
                          outline: "none",
                        }}
                      >
                        Copy Link
                      </button>
                      {i.is_active && (
                        <button
                          onClick={() => handleRevoke(i.id)}
                          style={{
                            padding: "4px 8px",
                            borderRadius: "4px",
                            border: "1px solid var(--color-error)",
                            background: "var(--color-error-glow)",
                            color: "var(--color-error)",
                            cursor: "pointer",
                            fontSize: "11px",
                            outline: "none",
                          }}
                        >
                          Revoke
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
            </table>

        </div>
      </div>
    </DashboardLayout>
  );
}


