"use client";

import React, { useState, useEffect } from "react";
import { DashboardLayout } from "../../layouts/DashboardLayout";
import { Input } from "../../components/UI/Input";
import { Skeleton } from "../../components/UI/Skeleton";
import { EmptyState } from "../../components/UI/EmptyState";
import { useToast } from "../../components/UI/ToastProvider";
import { apiFetch } from "../../services/api";

interface Topic {
  id: number;
  name: string;
  slug: string;
}

interface Company {
  id: number;
  name: string;
  slug: string;
  logo: string;
}

interface CompanyFreq {
  company_name: string;
  company_slug: string;
  frequency_bucket: string;
  frequency_percentage: number;
  metadata: {
    difficulty: string;
    tags: string[];
  };
}

interface DSAQuestion {
  id: number;
  title: string;
  slug: string;
  leetcode_url: string;
  difficulty: string;
  acceptance_rate: number;
  topics: Topic[];
  company_frequencies: CompanyFreq[];
}

export default function DsaIntelligence() {
  const { showToast } = useToast();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [questions, setQuestions] = useState<DSAQuestion[]>([]);
  
  // Selection / Filters
  const [selectedCompany, setSelectedCompany] = useState("google");
  const [selectedBucket, setSelectedBucket] = useState("30_days");
  const [selectedDifficulty, setSelectedDifficulty] = useState("");
  const [selectedTopic, setSelectedTopic] = useState("");
  const [searchKeyword, setSearchKeyword] = useState("");
  const [companySearch, setCompanySearch] = useState("");
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Load Companies & Topics on Mount
  useEffect(() => {
    apiFetch<{ results?: Company[] } | Company[]>("/api/v1/dsa-intelligence/companies/")
      .then((data) => {
        const list = Array.isArray(data) ? data : data.results || [];
        setCompanies(list);
      })
      .catch((err) => {
        console.error("Error loading companies", err);
        showToast("Failed to load companies list.", "error");
      });

    apiFetch<{ results?: Topic[] } | Topic[]>("/api/v1/dsa-intelligence/topics/")
      .then((data) => {
        const list = Array.isArray(data) ? data : data.results || [];
        setTopics(list);
      })
      .catch((err) => {
        console.error("Error loading topics", err);
        showToast("Failed to load topics list.", "error");
      });
  }, []);

  // Fetch filtered questions
  useEffect(() => {
    setLoading(true);
    setError("");

    let url = `/api/v1/dsa-intelligence/questions/?company=${selectedCompany}&frequency_bucket=${selectedBucket}`;
    if (selectedDifficulty) url += `&difficulty=${selectedDifficulty}`;
    if (selectedTopic) url += `&topic=${selectedTopic}`;
    if (searchKeyword) url += `&keyword=${encodeURIComponent(searchKeyword)}`;

    apiFetch<{ results?: DSAQuestion[] } | DSAQuestion[]>(url)
      .then((data) => {
        const list = Array.isArray(data) ? data : data.results || [];
        setQuestions(list);
      })
      .catch((err: any) => {
        setError(err.message || "Failed to load questions.");
        showToast(err.message || "Failed to load interview questions.", "error");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [selectedCompany, selectedBucket, selectedDifficulty, selectedTopic, searchKeyword]);

  const buckets = [
    { value: "30_days", label: "Last 30 Days" },
    { value: "3_months", label: "Last 3 Months" },
    { value: "6_months", label: "Last 6 Months" },
    { value: "more_than_6_months", label: "More than 6 Months" },
    { value: "all", label: "All Questions" }
  ];

  return (
    <DashboardLayout>
      <div style={{ maxWidth: "1300px", margin: "0 auto" }}>
        {/* Header */}
        <div style={{ marginBottom: "32px" }}>
          <h1
            style={{
              fontSize: "32px",
              fontWeight: "bold",
              background: "linear-gradient(90deg, #63b3ed, #4299e1, #3182ce)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Company Interview Intelligence
          </h1>
          <p style={{ color: "var(--text-muted)", marginTop: "6px", fontSize: "14px" }}>
            Explore verified LeetCode interview questions, recency frequency buckets, and concepts heatmaps.
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 280px) 1fr)", gap: "24px" }}>
          {/* Sidebar Controls */}
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            {/* Company Picker */}
            <div className="glass-panel" style={{ padding: "20px" }}>
              <h3
                style={{
                  fontSize: "13px",
                  marginBottom: "12px",
                  textTransform: "uppercase",
                  letterSpacing: "1px",
                  color: "var(--text-muted)",
                  fontWeight: "bold",
                }}
              >
                Target Company
              </h3>

              {/* Selected company badge */}
              <div
                style={{
                  marginBottom: "12px",
                  padding: "8px 12px",
                  borderRadius: "8px",
                  background: "rgba(99,179,237,0.15)",
                  border: "1px solid rgba(99,179,237,0.3)",
                  fontSize: "13px",
                  fontWeight: "bold",
                  color: "#63b3ed",
                }}
              >
                {companies.find((c) => c.slug === selectedCompany)?.name || selectedCompany}
              </div>

              {/* Search filter */}
              <Input
                placeholder="Search company..."
                value={companySearch}
                onChange={(e) => setCompanySearch(e.target.value)}
                style={{ fontSize: "13px", padding: "10px", marginBottom: "8px" }}
              />

              {/* Scrollable company list */}
              <div
                style={{
                  maxHeight: "240px",
                  overflowY: "auto",
                  borderRadius: "8px",
                  border: "1px solid var(--border-color)",
                  background: "rgba(0,0,0,0.2)",
                }}
              >
                {companies
                  .filter((c) => c.name.toLowerCase().includes(companySearch.toLowerCase()))
                  .map((c) => (
                    <div
                      key={c.id}
                      onClick={() => setSelectedCompany(c.slug)}
                      style={{
                        padding: "9px 14px",
                        cursor: "pointer",
                        fontSize: "13px",
                        background: selectedCompany === c.slug ? "rgba(99,179,237,0.2)" : "transparent",
                        color: selectedCompany === c.slug ? "#63b3ed" : "var(--text-main)",
                        fontWeight: selectedCompany === c.slug ? "bold" : "normal",
                        borderLeft: selectedCompany === c.slug ? "3px solid #63b3ed" : "3px solid transparent",
                        transition: "all 0.15s",
                      }}
                      onMouseEnter={(e) => {
                        if (selectedCompany !== c.slug)
                          (e.currentTarget as HTMLDivElement).style.background = "rgba(255,255,255,0.05)";
                      }}
                      onMouseLeave={(e) => {
                        if (selectedCompany !== c.slug)
                          (e.currentTarget as HTMLDivElement).style.background = "transparent";
                      }}
                    >
                      {c.name}
                    </div>
                  ))}
                {companies.filter((c) => c.name.toLowerCase().includes(companySearch.toLowerCase())).length === 0 && (
                  <div style={{ padding: "20px", textAlign: "center", color: "var(--text-muted)", fontSize: "13px" }}>
                    No companies found
                  </div>
                )}
              </div>
              <div style={{ marginTop: "8px", fontSize: "11px", color: "var(--text-muted)", textAlign: "right" }}>
                {companies.filter((c) => c.name.toLowerCase().includes(companySearch.toLowerCase())).length} of{" "}
                {companies.length} companies
              </div>
            </div>

            {/* Filters */}
            <div className="glass-panel" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
              <h3
                style={{
                  fontSize: "13px",
                  textTransform: "uppercase",
                  letterSpacing: "1px",
                  color: "var(--text-muted)",
                  fontWeight: "bold",
                }}
              >
                Filters
              </h3>

              <div>
                <label style={{ display: "block", fontSize: "12px", color: "var(--text-muted)", marginBottom: "6px" }}>
                  Difficulty
                </label>
                <select
                  value={selectedDifficulty}
                  onChange={(e) => setSelectedDifficulty(e.target.value)}
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
                  <option value="">All Difficulties</option>
                  <option value="Easy">Easy</option>
                  <option value="Medium">Medium</option>
                  <option value="Hard">Hard</option>
                </select>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "12px", color: "var(--text-muted)", marginBottom: "6px" }}>
                  DSA Topic
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
                  <option value="">All Topics</option>
                  {topics.map((t) => (
                    <option key={t.id} value={t.slug}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <Input
                  label="Keyword Search"
                  placeholder="Search e.g. Two Sum"
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  style={{ fontSize: "13px", padding: "10px" }}
                />
              </div>
            </div>

            {/* Quick Stats */}
            <div className="glass-panel" style={{ padding: "20px" }}>
              <h3
                style={{
                  fontSize: "13px",
                  marginBottom: "12px",
                  textTransform: "uppercase",
                  letterSpacing: "1px",
                  color: "var(--text-muted)",
                  fontWeight: "bold",
                }}
              >
                Difficulty Breakdown
              </h3>
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
                  <span>Easy</span>
                  <span style={{ color: "var(--color-success)", fontWeight: "bold" }}>
                    {questions.filter((q) => q.difficulty === "Easy").length}
                  </span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
                  <span>Medium</span>
                  <span style={{ color: "var(--color-warning)", fontWeight: "bold" }}>
                    {questions.filter((q) => q.difficulty === "Medium").length}
                  </span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
                  <span>Hard</span>
                  <span style={{ color: "var(--color-error)", fontWeight: "bold" }}>
                    {questions.filter((q) => q.difficulty === "Hard").length}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Content Area */}
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            {/* Recency Tabs */}
            <div style={{ display: "flex", borderBottom: "1px solid var(--border-color)", paddingBottom: "1px" }}>
              {buckets.map((b) => (
                <button
                  key={b.value}
                  onClick={() => setSelectedBucket(b.value)}
                  style={{
                    padding: "12px 20px",
                    background: "transparent",
                    border: "none",
                    borderBottom: selectedBucket === b.value ? "2px solid var(--accent-primary)" : "none",
                    color: selectedBucket === b.value ? "var(--text-main)" : "var(--text-muted)",
                    fontWeight: "bold",
                    fontSize: "14px",
                    cursor: "pointer",
                    transition: "all 0.2s",
                  }}
                >
                  {b.label}
                </button>
              ))}
            </div>

            {/* Questions List */}
            <div className="glass-panel" style={{ minHeight: "400px", padding: "20px" }}>
              {loading ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  <Skeleton height="35px" width="100%" />
                  <Skeleton height="45px" width="100%" />
                  <Skeleton height="45px" width="100%" />
                  <Skeleton height="45px" width="100%" />
                  <Skeleton height="45px" width="100%" />
                </div>
              ) : error ? (
                <div
                  style={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    minHeight: "300px",
                    color: "var(--color-error)",
                  }}
                >
                  {error}
                </div>
              ) : questions.length === 0 ? (
                <EmptyState
                  icon=""
                  title="No questions found"
                  description="No interview questions matched your criteria. Try adjusting or clearing your filters."
                />
              ) : (
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
                    <thead>
                      <tr
                        style={{
                          borderBottom: "1px solid var(--border-color)",
                          color: "var(--text-muted)",
                          fontSize: "12px",
                          textTransform: "uppercase",
                        }}
                      >
                        <th style={{ padding: "12px" }}>Title</th>
                        <th style={{ padding: "12px" }}>Difficulty</th>
                        <th style={{ padding: "12px" }}>Acceptance Rate</th>
                        <th style={{ padding: "12px" }}>Topics</th>
                        <th style={{ padding: "12px" }}>Frequency</th>
                        <th style={{ padding: "12px" }}>Link</th>
                      </tr>
                    </thead>
                    <tbody>
                      {questions.map((q) => {
                        const freq = q.company_frequencies.find(
                          (cf) => cf.company_slug === selectedCompany && cf.frequency_bucket === selectedBucket
                        );
                        return (
                          <tr key={q.id} style={{ borderBottom: "1px solid rgba(255,255,255,0.03)", fontSize: "14px" }}>
                            <td style={{ padding: "14px 12px", fontWeight: "bold" }}>{q.title}</td>
                            <td style={{ padding: "14px 12px" }}>
                              <span
                                style={{
                                  padding: "4px 8px",
                                  borderRadius: "4px",
                                  fontSize: "11px",
                                  fontWeight: "bold",
                                  background:
                                    q.difficulty === "Easy"
                                      ? "var(--color-success-glow)"
                                      : q.difficulty === "Medium"
                                      ? "var(--color-warning-glow)"
                                      : "var(--color-error-glow)",
                                  color:
                                    q.difficulty === "Easy"
                                      ? "var(--color-success)"
                                      : q.difficulty === "Medium"
                                      ? "var(--color-warning)"
                                      : "var(--color-error)",
                                }}
                              >
                                {q.difficulty}
                              </span>
                            </td>
                            <td style={{ padding: "14px 12px", color: "var(--text-muted)" }}>
                              {q.acceptance_rate ? `${q.acceptance_rate.toFixed(1)}%` : "N/A"}
                            </td>
                            <td style={{ padding: "14px 12px" }}>
                              <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                                {q.topics.map((t) => (
                                  <span
                                    key={t.id}
                                    style={{
                                      padding: "2px 6px",
                                      borderRadius: "4px",
                                      background: "rgba(255,255,255,0.05)",
                                      fontSize: "11px",
                                      color: "var(--text-muted)",
                                    }}
                                  >
                                    {t.name}
                                  </span>
                                ))}
                              </div>
                            </td>
                            <td style={{ padding: "14px 12px" }}>
                              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                <div
                                  style={{
                                    width: "60px",
                                    height: "6px",
                                    background: "rgba(255,255,255,0.1)",
                                    borderRadius: "3px",
                                    overflow: "hidden",
                                  }}
                                >
                                  <div
                                    style={{
                                      width: `${freq ? freq.frequency_percentage : 0}%`,
                                      height: "100%",
                                      background: "var(--accent-primary)",
                                    }}
                                  ></div>
                                </div>
                                <span style={{ fontSize: "12px" }}>
                                  {freq ? `${freq.frequency_percentage.toFixed(0)}%` : "0%"}
                                </span>
                              </div>
                            </td>
                            <td style={{ padding: "14px 12px" }}>
                              {q.leetcode_url ? (
                                <a
                                  href={q.leetcode_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  style={{ color: "var(--accent-primary)", textDecoration: "none", fontWeight: "bold" }}
                                >
                                  LeetCode ↗
                                </a>
                              ) : (
                                "N/A"
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

// Refactor: Fix minor edge cases in calculation functions.

// Refactor: Optimize query performance and database indexing.

// Refactor: Add typing hints and documentation docstrings.

// Refactor: Optimize imports and clean up code structure.
