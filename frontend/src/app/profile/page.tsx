"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "../../layouts/DashboardLayout";
import { useAuth } from "../../hooks/useAuth";
import { useToast } from "../../components/UI/ToastProvider";
import { Input } from "../../components/UI/Input";
import { Button } from "../../components/UI/Button";
import { apiFetch, authFetch } from "../../services/api";

interface Session {
  id: number;
  session_key: string;
  device_info: string;
  ip_address: string;
  last_activity: string;
  created_at: string;
}

interface AuditLog {
  id: number;
  action: string;
  ip_address: string;
  user_agent: string;
  timestamp: string;
}

export default function Profile() {
  const router = useRouter();
  const { user, token } = useAuth();
  const { showToast } = useToast();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [isEmailVerified, setIsEmailVerified] = useState(false);
  const [profileImage, setProfileImage] = useState<string | null>(null);

  const [sessions, setSessions] = useState<Session[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) return;

    // Fetch user details
    apiFetch<{ email: string; first_name: string; last_name: string; is_email_verified: boolean; profile_image: string | null }>(
      "/api/v1/auth/me/"
    )
      .then((data) => {
        setEmail(data.email);
        setFirstName(data.first_name || "");
        setLastName(data.last_name || "");
        setIsEmailVerified(data.is_email_verified);
        setProfileImage(data.profile_image);
      })
      .catch((err) => {
        console.error("Error loading user profile", err);
        showToast("Failed to load user profile data.", "error");
      });

    // Fetch active sessions
    apiFetch<Session[]>("/api/v1/auth/sessions/")
      .then((data) => setSessions(data))
      .catch((err) => console.error("Error loading sessions", err));

    // Fetch audit logs
    apiFetch<AuditLog[]>("/api/v1/auth/audit-logs/")
      .then((data) => setAuditLogs(data))
      .catch((err) => console.error("Error loading audit logs", err));
  }, [token]);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await authFetch("/api/v1/auth/me/", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          first_name: firstName,
          last_name: lastName,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Update failed.");
      }

      showToast("Profile details updated successfully!", "success");
    } catch (err: any) {
      showToast(err.message || "Failed to update profile.", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);

    const formData = new FormData();
    formData.append("profile_image", file);

    try {
      const response = await authFetch("/api/v1/auth/me/", {
        method: "PATCH",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Image upload failed.");
      }

      const data = await response.json();
      setProfileImage(data.profile_image);
      showToast("Profile image updated successfully!", "success");
    } catch (err: any) {
      showToast(err.message || "Failed to upload image.", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
        {/* Header */}
        <div style={{ marginBottom: "32px" }}>
          <h1
            style={{
              fontSize: "32px",
              fontWeight: "bold",
              background: "linear-gradient(90deg, var(--accent-primary), var(--accent-secondary))",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Profile & Account Center
          </h1>
          <p style={{ color: "var(--text-muted)", marginTop: "6px", fontSize: "14px" }}>
            Manage details, monitor logins, track device sessions, and view audit history.
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "24px" }}>
          {/* Profile Card & Details Form */}
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            <div
              className="glass-panel"
              style={{
                padding: "24px",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                textAlign: "center",
              }}
            >
              <div
                style={{
                  position: "relative",
                  width: "120px",
                  height: "120px",
                  borderRadius: "50%",
                  overflow: "hidden",
                  background: "rgba(255,255,255,0.05)",
                  border: "2px solid var(--accent-primary)",
                  marginBottom: "16px",
                }}
              >
                {profileImage ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={profileImage}
                    alt="Profile"
                    style={{ width: "100%", height: "100%", objectFit: "cover" }}
                  />
                ) : (
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "center",
                      alignItems: "center",
                      height: "100%",
                      fontSize: "40px",
                    }}
                  >
                    
                  </div>
                )}
              </div>

              <h3 style={{ fontSize: "18px", fontWeight: "bold" }}>
                {firstName} {lastName}
              </h3>
              <p style={{ color: "var(--text-muted)", fontSize: "13px", marginTop: "4px" }}>{email}</p>

              <span
                style={{
                  marginTop: "12px",
                  padding: "4px 10px",
                  borderRadius: "12px",
                  fontSize: "11px",
                  fontWeight: "bold",
                  background: isEmailVerified ? "var(--color-success-glow)" : "var(--color-error-glow)",
                  color: isEmailVerified ? "var(--color-success)" : "var(--color-error)",
                }}
              >
                {isEmailVerified ? "Verified Account" : "Unverified Account"}
              </span>

              <div style={{ marginTop: "20px" }}>
                <label
                  style={{
                    padding: "8px 16px",
                    borderRadius: "6px",
                    border: "1px solid var(--border-color)",
                    background: "rgba(255,255,255,0.03)",
                    fontSize: "13px",
                    cursor: "pointer",
                    transition: "background 0.2s",
                    display: "inline-block",
                  }}
                >
                  Upload Profile Image
                  <input type="file" accept="image/*" onChange={handleImageUpload} style={{ display: "none" }} />
                </label>
              </div>
            </div>

            <div className="glass-panel" style={{ padding: "24px" }}>
              <h2 style={{ fontSize: "18px", fontWeight: "bold", marginBottom: "16px" }}>Edit Details</h2>

              <form onSubmit={handleUpdateProfile} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <Input
                  label="First Name"
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  required
                />

                <Input
                  label="Last Name"
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  required
                />

                <Button type="submit" isLoading={loading}>
                  Save Profile Details
                </Button>
              </form>
            </div>
          </div>

          {/* Sessions & Audit History Section */}
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            {/* Active Sessions */}
            <div className="glass-panel" style={{ padding: "24px", maxHeight: "320px", overflowY: "auto" }}>
              <h2 style={{ fontSize: "18px", fontWeight: "bold", marginBottom: "16px" }}>Active Sessions</h2>
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {sessions.map((s) => (
                  <div
                    key={s.id}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "12px",
                      borderRadius: "8px",
                      background: "rgba(255,255,255,0.01)",
                      border: "1px solid var(--border-color)",
                      fontSize: "13px",
                    }}
                  >
                    <div>
                      <span style={{ fontWeight: "bold", display: "block" }}>IP: {s.ip_address || "Unknown"}</span>
                      <span style={{ color: "var(--text-muted)", display: "block", fontSize: "11px", marginTop: "2px" }}>
                        {s.device_info || "Unknown Browser"}
                      </span>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                        Last seen: {new Date(s.last_activity).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Audit Logs */}
            <div className="glass-panel" style={{ padding: "24px", maxHeight: "380px", overflowY: "auto" }}>
              <h2 style={{ fontSize: "18px", fontWeight: "bold", marginBottom: "16px" }}>Security Audit Logs</h2>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {auditLogs.map((l) => (
                  <div
                    key={l.id}
                    style={{
                      padding: "10px 15px",
                      borderRadius: "6px",
                      background: "rgba(255,255,255,0.01)",
                      border: "1px solid var(--border-color)",
                      display: "flex",
                      justifyContent: "space-between",
                      fontSize: "13px",
                    }}
                  >
                    <div>
                      <span style={{ fontFamily: "var(--font-mono)", color: "var(--accent-primary)" }}>{l.action}</span>
                      <span style={{ color: "var(--text-muted)", display: "block", fontSize: "11px", marginTop: "2px" }}>
                        IP: {l.ip_address || "Unknown"}
                      </span>
                    </div>
                    <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                      {new Date(l.timestamp).toLocaleDateString()} {new Date(l.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

// Refactor: Improve error handling and exception logging.

// Refactor: Optimize query performance and database indexing.
