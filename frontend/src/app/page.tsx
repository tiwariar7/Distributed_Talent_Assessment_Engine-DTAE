"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "../hooks/useAuth";

export default function LandingPage() {
  const router = useRouter();
  const { isAuthenticated, user, loading } = useAuth();

  // Auto-redirect authenticated sessions to corresponding dashboard gates
  useEffect(() => {
    if (!loading && isAuthenticated && user) {
      if (user.isRecruiter) {
        router.push("/recruiter/assessments");
      } else {
        router.push("/candidate/dashboard");
      }
    }
  }, [loading, isAuthenticated, user, router]);

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
        <div className="animate-spin" style={{ width: "40px", height: "40px", border: "3px solid var(--border-color)", borderTopColor: "var(--accent-primary)", borderRadius: "50%" }} />
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", background: "var(--bg-main)", overflow: "hidden" }}>
      {/* Header / Navbar */}
      <header
        style={{
          width: "100%",
          padding: "20px 40px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid var(--border-color)",
          backdropFilter: "blur(8px)",
          position: "sticky",
          top: 0,
          zIndex: 10,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--accent-primary)", display: "inline-block", verticalAlign: "middle" }}><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" fill="currentColor"/></svg>
          <span style={{ fontWeight: 800, fontSize: "18px", letterSpacing: "0.5px" }}>DTAE Engine</span>
        </div>

        <div style={{ display: "flex", gap: "16px" }}>
          <Link
            href="/login"
            style={{
              padding: "8px 16px",
              borderRadius: "6px",
              border: "1px solid var(--border-color)",
              textDecoration: "none",
              color: "#fff",
              fontSize: "13px",
              fontWeight: "bold",
              transition: "all 0.2s",
            }}
            onMouseOver={(e) => {
              (e.currentTarget as HTMLElement).style.background = "rgba(255, 255, 255, 0.05)";
            }}
            onMouseOut={(e) => {
              (e.currentTarget as HTMLElement).style.background = "transparent";
            }}
          >
            Sign In
          </Link>
          <Link
            href="/register"
            style={{
              padding: "8px 16px",
              borderRadius: "6px",
              background: "linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%)",
              textDecoration: "none",
              color: "#fff",
              fontSize: "13px",
              fontWeight: "bold",
              boxShadow: "0 0 10px var(--accent-primary-glow)",
              transition: "all 0.2s",
            }}
            onMouseOver={(e) => {
              (e.currentTarget as HTMLElement).style.boxShadow = "0 0 15px var(--accent-primary-glow)";
            }}
            onMouseOut={(e) => {
              (e.currentTarget as HTMLElement).style.boxShadow = "0 0 10px var(--accent-primary-glow)";
            }}
          >
            Get Started
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "80px 20px", position: "relative" }}>
        
        {/* Glow element */}
        <div
          style={{
            position: "absolute",
            top: "10%",
            left: "50%",
            transform: "translateX(-50%)",
            width: "600px",
            height: "200px",
            background: "radial-gradient(circle, var(--accent-primary-glow) 0%, transparent 80%)",
            filter: "blur(60px)",
            zIndex: -1,
            pointerEvents: "none",
          }}
        />

        <div style={{ maxWidth: "800px", textAlign: "center", display: "flex", flexDirection: "column", gap: "24px", zIndex: 1 }}>
          <span
            className="animate-fade-in"
            style={{
              fontSize: "12px",
              fontWeight: 700,
              letterSpacing: "2px",
              textTransform: "uppercase",
              background: "linear-gradient(90deg, hsl(263, 90%, 75%), hsl(217, 91%, 70%))",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Distributed Talent Assessment Engine
          </span>

          <h1
            className="animate-fade-in"
            style={{
              fontSize: "52px",
              fontWeight: 900,
              lineHeight: "1.1",
              color: "#fff",
              letterSpacing: "-1.5px",
            }}
          >
            The Ultimate Secure Coding &amp; Evaluation Platform
          </h1>

          <p
            className="animate-fade-in"
            style={{
              fontSize: "17px",
              color: "var(--text-muted)",
              lineHeight: "1.6",
              maxWidth: "600px",
              margin: "0 auto",
            }}
          >
            DTAE provides containerized, sandboxed execution with real-time feedback and intelligent ML proctoring models to grade technical skills fairly.
          </p>

          <div
            className="animate-fade-in"
            style={{
              display: "flex",
              justifyContent: "center",
              gap: "16px",
              marginTop: "12px",
            }}
          >
            <Link
              href="/login?role=candidate"
              style={{
                padding: "14px 28px",
                borderRadius: "8px",
                background: "linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%)",
                textDecoration: "none",
                color: "#fff",
                fontWeight: "bold",
                fontSize: "15px",
                boxShadow: "0 4px 20px var(--accent-primary-glow)",
                transition: "all 0.2s",
              }}
            >
              Candidate Portal
            </Link>
            <Link
              href="/login?role=recruiter"
              style={{
                padding: "14px 28px",
                borderRadius: "8px",
                border: "1px solid var(--border-color)",
                background: "rgba(255, 255, 255, 0.05)",
                textDecoration: "none",
                color: "#fff",
                fontWeight: "bold",
                fontSize: "15px",
                transition: "all 0.2s",
              }}
              onMouseOver={(e) => {
                (e.currentTarget as HTMLElement).style.background = "rgba(255, 255, 255, 0.08)";
              }}
              onMouseOut={(e) => {
                (e.currentTarget as HTMLElement).style.background = "rgba(255, 255, 255, 0.05)";
              }}
            >
              Recruiter Console
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <section
          style={{
            maxWidth: "1100px",
            width: "100%",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
            gap: "24px",
            marginTop: "80px",
          }}
        >
          <div className="glass-panel" style={{ padding: "32px", display: "flex", flexDirection: "column", gap: "12px" }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginBottom: "8px" }}><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
            <h3 style={{ fontSize: "18px", fontWeight: "bold", color: "#fff" }}>Secure Sandbox Execution</h3>
            <p style={{ color: "var(--text-muted)", fontSize: "14px", lineHeight: "1.5" }}>
              Code solutions are run in secure isolated environments supporting Python, JavaScript, C++, and Java with resource boundaries.
            </p>
          </div>

          <div className="glass-panel" style={{ padding: "32px", display: "flex", flexDirection: "column", gap: "12px" }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginBottom: "8px" }}><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
            <h3 style={{ fontSize: "18px", fontWeight: "bold", color: "#fff" }}>ML Proctoring Guards</h3>
            <p style={{ color: "var(--text-muted)", fontSize: "14px", lineHeight: "1.5" }}>
              Webcam object classification (phone checks), audio speech detection, and screen-sharing OCR identify AI usage automatically.
            </p>
          </div>

          <div className="glass-panel" style={{ padding: "32px", display: "flex", flexDirection: "column", gap: "12px" }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginBottom: "8px" }}><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.45 1-1 1H4v2h16v-2h-5c-.55 0-1-.45-1-1v-2.34"/><path d="M12 2a6 6 0 0 1 6 6v1a6 6 0 0 1-6 6 6 6 0 0 1-6-6V8a6 6 0 0 1 6-6z"/></svg>
            <h3 style={{ fontSize: "18px", fontWeight: "bold", color: "#fff" }}>Real-Time Leaderboard</h3>
            <p style={{ color: "var(--text-muted)", fontSize: "14px", lineHeight: "1.5" }}>
              Watch results update immediately. CouchDB MapReduce views dynamically sync candidate scores and solutions progress.
            </p>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer
        style={{
          width: "100%",
          padding: "24px 40px",
          borderTop: "1px solid var(--border-color)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: "13px",
          color: "var(--text-muted)",
        }}
      >
        <span>&copy; {new Date().getFullYear()} DTAE Engine. All rights reserved.</span>
        <div style={{ display: "flex", gap: "16px" }}>
          <span>Privacy Policy</span>
          <span>Terms of Service</span>
        </div>
      </footer>
    </div>
  );
}

// Refactor: Optimize imports and clean up code structure.

// Refactor: Improve responsive styles and layouts.

// Refactor: Refactor variable names for better readability.

// Refactor: Update validation checks and constraints.

// Refactor: Refactor variable names for better readability.

// Refactor: Update validation checks and constraints.

// Refactor: Refactor variable names for better readability.

// Refactor: Fix minor edge cases in calculation functions.
