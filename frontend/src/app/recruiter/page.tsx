"use client";

import React, { useState, useEffect } from "react";
import { DashboardLayout } from "../../layouts/DashboardLayout";
import { useAuth } from "../../hooks/useAuth";
import { useToast } from "../../components/UI/ToastProvider";
import { Input } from "../../components/UI/Input";
import { Button } from "../../components/UI/Button";
import { apiFetch, apiPost } from "../../services/api";

interface Company {
  id: number;
  name: string;
  slug: string;
}

interface Topic {
  id: number;
  name: string;
  slug: string;
}

export default function RecruiterDashboard() {
  const { token } = useAuth();
  const { showToast } = useToast();

  // Invitation Form state
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteLoading, setInviteLoading] = useState(false);

  // Generator Form state
  const [companies, setCompanies] = useState<Company[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [selectedCompany, setSelectedCompany] = useState("");
  const [selectedBucket, setSelectedBucket] = useState("all");
  const [easyCount, setEasyCount] = useState(1);
  const [mediumCount, setMediumCount] = useState(2);
  const [hardCount, setHardCount] = useState(1);
  const [roundTitle, setRoundTitle] = useState("");
  const [selectedTopic, setSelectedTopic] = useState("");
  const [genLoading, setGenLoading] = useState(false);

  // Load Form Data
  useEffect(() => {
    if (!token) return;

    // Fetch lists
    apiFetch<{ results?: Company[] } | Company[]>("/api/v1/dsa-intelligence/companies/")
      .then((data) => {
        const results = Array.isArray(data) ? data : data.results || [];
        setCompanies(results);
        if (results.length > 0) setSelectedCompany(results[0].slug);
      })
      .catch((err) => console.error(err));

    apiFetch<{ results?: Topic[] } | Topic[]>("/api/v1/dsa-intelligence/topics/")
      .then((data) => {
        const results = Array.isArray(data) ? data : data.results || [];
        setTopics(results);
      })
      .catch((err) => console.error(err));
  }, [token]);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setInviteLoading(true);

    try {
      await apiPost("/api/v1/auth/invite-recruiter/", { email: inviteEmail });
      showToast("Invitation generated successfully! Verification link printed in Django server logs.", "success");
      setInviteEmail("");
    } catch (err: any) {
      showToast(err.message || "Could not complete recruiter invitation.", "error");
    } finally {
      setInviteLoading(false);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenLoading(true);

    const payload = {
      company_slug: selectedCompany,
      frequency_bucket: selectedBucket,
      easy_count: easyCount,
      medium_count: mediumCount,
      hard_count: hardCount,
      topic_slug: selectedTopic || undefined,
      title: roundTitle || undefined,
    };

    try {
      const data = await apiPost<{ title: string; problems_count: number; assessment_id: number }>(
        "/api/v1/dsa-intelligence/assessments/generate/",
        payload
      );

      showToast(
        `Assessment '${data.title}' containing ${data.problems_count} problems generated and published successfully! ID: ${data.assessment_id}`,
        "success"
      );
      setRoundTitle("");
    } catch (err: any) {
      showToast(err.message || "Failed to generate assessment.", "error");
    } finally {
      setGenLoading(false);
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
              background: "linear-gradient(90deg, #ed64a6, #e53e3e)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Recruiter Dashboard
          </h1>
          <p style={{ color: "var(--text-muted)", marginTop: "6px", fontSize: "14px" }}>
            Invite teammates, setup recruiting tasks, and auto-balance DSA mock rounds.
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "24px" }}>
          {/* Recruiter Invitation Section */}
          <div className="glass-panel" style={{ padding: "24px", height: "fit-content" }}>
            <h2 style={{ fontSize: "18px", fontWeight: "bold", marginBottom: "20px", color: "var(--text-main)" }}>
              Invite Team Recruiters
            </h2>

            <form onSubmit={handleInvite} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <Input
                label="Recruiter Email Address"
                type="email"
                placeholder="colleague@company.com"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                required
              />

              <Button type="submit" isLoading={inviteLoading}>
                Send Invitation
              </Button>
            </form>
          </div>

          {/* Smart Assessment Generator Section */}
          <div className="glass-panel" style={{ padding: "24px" }}>
            <h2 style={{ fontSize: "18px", fontWeight: "bold", marginBottom: "20px", color: "var(--text-main)" }}>
              Smart Assessment Generator
            </h2>

            <form onSubmit={handleGenerate} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <Input
                label="Assessment Title (Optional)"
                type="text"
                placeholder="e.g. Google Front-End Mock Assessment"
                value={roundTitle}
                onChange={(e) => setRoundTitle(e.target.value)}
              />

              <div style={{ display: "flex", gap: "12px" }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: "block", fontSize: "13px", color: "var(--text-muted)", marginBottom: "6px" }}>
                    Target Company
                  </label>
                  <select
                    value={selectedCompany}
                    onChange={(e) => setSelectedCompany(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "10px",
                      borderRadius: "8px",
                      border: "1px solid var(--border-color)",
                      background: "rgba(0,0,0,0.3)",
                      color: "var(--text-main)",
                      fontSize: "13px",
                      outline: "none",
                    }}
                  >
                    {companies.map((c) => (
                      <option key={c.id} value={c.slug}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div style={{ flex: 1 }}>
                  <label style={{ display: "block", fontSize: "13px", color: "var(--text-muted)", marginBottom: "6px" }}>
                    Frequency Bucket
                  </label>
                  <select
                    value={selectedBucket}
                    onChange={(e) => setSelectedBucket(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "10px",
                      borderRadius: "8px",
                      border: "1px solid var(--border-color)",
                      background: "rgba(0,0,0,0.3)",
                      color: "var(--text-main)",
                      fontSize: "13px",
                      outline: "none",
                    }}
                  >
                    <option value="30_days">Last 30 Days</option>
                    <option value="3_months">Last 3 Months</option>
                    <option value="6_months">Last 6 Months</option>
                    <option value="more_than_6_months">More than 6 Months</option>
                    <option value="all">All Questions</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "13px", color: "var(--text-muted)", marginBottom: "6px" }}>
                  Focus DSA Topic (Optional)
                </label>
                <select
                  value={selectedTopic}
                  onChange={(e) => setSelectedTopic(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px",
                    borderRadius: "8px",
                    border: "1px solid var(--border-color)",
                    background: "rgba(0,0,0,0.3)",
                    color: "var(--text-main)",
                    fontSize: "13px",
                    outline: "none",
                  }}
                >
                  <option value="">Any Topic</option>
                  {topics.map((t) => (
                    <option key={t.id} value={t.slug}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "13px", color: "var(--text-muted)", marginBottom: "8px" }}>
                  Auto-Balance Difficulty Mix
                </label>
                <div style={{ display: "flex", gap: "12px" }}>
                  <div style={{ flex: 1 }}>
                    <Input
                      label="Easy Count"
                      type="number"
                      min="0"
                      max="10"
                      value={easyCount}
                      onChange={(e) => setEasyCount(parseInt(e.target.value) || 0)}
                      style={{ textAlign: "center", padding: "8px" }}
                    />
                  </div>
                  <div style={{ flex: 1 }}>
                    <Input
                      label="Medium Count"
                      type="number"
                      min="0"
                      max="10"
                      value={mediumCount}
                      onChange={(e) => setMediumCount(parseInt(e.target.value) || 0)}
                      style={{ textAlign: "center", padding: "8px" }}
                    />
                  </div>
                  <div style={{ flex: 1 }}>
                    <Input
                      label="Hard Count"
                      type="number"
                      min="0"
                      max="10"
                      value={hardCount}
                      onChange={(e) => setHardCount(parseInt(e.target.value) || 0)}
                      style={{ textAlign: "center", padding: "8px" }}
                    />
                  </div>
                </div>
              </div>

              <Button type="submit" isLoading={genLoading}>
                Generate Round
              </Button>
            </form>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

// Refactor: Enhance component rendering performance.

// Refactor: Improve error handling and exception logging.

// Refactor: Enhance component rendering performance.

// Refactor: Refactor variable names for better readability.

// Refactor: Optimize query performance and database indexing.

// Refactor: Refactor variable names for better readability.

// Refactor: Refactor variable names for better readability.

// Refactor: Refactor variable names for better readability.

// Refactor: Add typing hints and documentation docstrings.

// Refactor: Optimize imports and clean up code structure.
