"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Editor from "@monaco-editor/react";
import styles from "./page.module.css";
import { useProctoring } from "../../../hooks/useProctoring";
import { getWsBase, apiFetch, apiPost, authFetch } from "../../../services/api";
import { useAuth } from "../../../hooks/useAuth";

interface Problem {
  id: number;
  title: string;
  prompt: string;
  language: string;
  max_score: number;
  time_limit_ms: number;
  memory_limit_mb: number;
  display_order: number;
}

interface Assessment {
  id: number;
  title: string;
  description: string;
  status: string;
  duration_minutes: number;
  organization: string;
  problems: Problem[];
}

interface LogEntry {
  id: string;
  message: string;
  type: "info" | "success" | "error" | "warning";
  details?: string;
  stdoutUrl?: string | null;
  stderrUrl?: string | null;
}

export default function ProctoredAssessmentPage() {
  const params = useParams();
  const router = useRouter();
  const token = params.token as string;

  // Invitation & Assessment state
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [invitationId, setInvitationId] = useState<string | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [selectedProblem, setSelectedProblem] = useState<Problem | null>(null);
  const [code, setCode] = useState("");

  // Exam phase status
  const [isSetupPhase, setIsSetupPhase] = useState(true);
  const [isExamActive, setIsExamActive] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [sessionId, setSessionId] = useState<number | null>(null);

  // Fullscreen block state
  const [isFullscreenExited, setIsFullscreenExited] = useState(false);

  // Warnings & Overlays state
  const [warningMessage, setWarningMessage] = useState<string | null>(null);
  const [warningCount, setWarningCount] = useState(0);

  // Timer & Logs
  const [timeLeft, setTimeLeft] = useState(3600);
  const [submissionStatus, setSubmissionStatus] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  // Stream preview refs
  const setupVideoRef = useRef<HTMLVideoElement | null>(null);
  const workspaceVideoRef = useRef<HTMLVideoElement | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const logsEndRef = useRef<HTMLDivElement | null>(null);

  // Handlers for warning events from hook
  const handleAutoSubmitted = useCallback((reason: string) => {
    setIsExamActive(false);
    setIsCompleted(true);
    setError(`Assessment auto-submitted: ${reason}`);
    
    // Call backend finish
    if (assessment) {
      finishAssessment(true);
    }
  }, [assessment]);

  const handleWarningIssued = useCallback((violationType: string, count: number) => {
    setWarningCount(count);
    const readableType = violationType.replace(/_/g, " ");

    // Check for critical violations that trigger immediate auto-submit
    if (["phone_detected", "multiple_faces_detected", "ai_usage_detected"].includes(violationType)) {
      handleAutoSubmitted(`Critical Proctoring Violation: Detected ${readableType}. Test terminated.`);
      return;
    }

    setWarningMessage(`Proctoring Violation: Detected ${readableType}. (Warning ${count} of 2)`);
  }, [handleAutoSubmitted]);

  // Hook up useProctoring
  const { token: userAccessToken } = useAuth();
  const userToken = userAccessToken || "";
  const {
    state: proctoringState,
    modelsLoaded,
    mediaStreamRef,
    screenStreamRef,
    startCameraAndMic,
    startScreenShare,
    sendTelemetry,
  } = useProctoring({
    invitationId: invitationId || "",
    token: userToken,
    maxWarnings: 2,
    isExamActive: isExamActive,
    onWarningIssued: handleWarningIssued,
    onAutoSubmitted: handleAutoSubmitted,
  });

  // Fetch invitation details
  useEffect(() => {
    if (!token) return;

    apiFetch<{ invitation_id: string; assessment: Assessment }>(`/api/v1/recruiter/invitation/${token}/`)
      .then((data) => {
        setInvitationId(data.invitation_id);
        setAssessment(data.assessment);
        setTimeLeft(data.assessment.duration_minutes * 60);
        if (data.assessment.problems && data.assessment.problems.length > 0) {
          setSelectedProblem(data.assessment.problems[0]);
        }
        setLoading(false);
      })
      .catch((err: unknown) => {
        console.error(err);
        setError(err instanceof Error ? err.message : "Failed to load assessment.");
        setLoading(false);
      });
  }, [token]);

  // Sync streams to video elements when phase changes or permissions granted
  useEffect(() => {
    if (isSetupPhase && setupVideoRef.current && mediaStreamRef.current) {
      setupVideoRef.current.srcObject = mediaStreamRef.current;
    }
  }, [isSetupPhase, mediaStreamRef.current, proctoringState.isCameraActive]);

  useEffect(() => {
    if (isExamActive && workspaceVideoRef.current && mediaStreamRef.current) {
      workspaceVideoRef.current.srcObject = mediaStreamRef.current;
    }
  }, [isExamActive, mediaStreamRef.current, proctoringState.isCameraActive]);

  // Fullscreen monitoring
  useEffect(() => {
    if (!isExamActive) return;

    const onFullscreenChange = () => {
      if (!document.fullscreenElement) {
        setIsFullscreenExited(true);
      } else {
        setIsFullscreenExited(false);
      }
    };

    document.addEventListener("fullscreenchange", onFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", onFullscreenChange);
  }, [isExamActive]);

  // Timer countdown
  useEffect(() => {
    if (!isExamActive || timeLeft <= 0) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          finishAssessment(false); // Time up auto submit
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isExamActive, timeLeft]);

  // Set default solution template when problem changes
  useEffect(() => {
    if (!selectedProblem) return;
    if (selectedProblem.language === "python") {
      setCode(`def solve():\n    # Write your solution here\n    # Read inputs using input()\n    pass\n\nsolve()\n`);
    } else if (selectedProblem.language === "javascript") {
      setCode(`const fs = require('fs');\n\nfunction solve() {\n    const input = fs.readFileSync('/dev/stdin', 'utf-8');\n    // Write your solution here\n}\n\nsolve();\n`);
    } else if (selectedProblem.language === "cpp") {
      setCode(`#include <iostream>\nusing namespace std;\n\nint main() {\n    // Write your solution here\n    return 0;\n}\n`);
    } else {
      setCode(`import java.util.Scanner;\n\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner scanner = new Scanner(System.in);\n        // Write your solution here\n    }\n}\n`);
    }
    setLogs([]);
    setSubmissionStatus(null);
  }, [selectedProblem]);

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  // Start Assessment Exam
  const handleStartAssessment = async () => {
    // 1. Double check authentication
    if (!userAccessToken) {
      setError("You must be signed in to take this assessment. Please sign in on the main dashboard first.");
      return;
    }

    try {
      // 2. Request Fullscreen
      if (document.documentElement.requestFullscreen) {
        await document.documentElement.requestFullscreen();
      }

      // 3. Register proctoring session on backend
      const sessionData = await apiPost<{ id: number }>("/api/v1/proctoring/session/start/", {
        invitation_token: token,
        is_camera_active: proctoringState.isCameraActive,
        is_mic_active: proctoringState.isMicActive,
        metadata: {
          screen_width: window.screen.width,
          screen_height: window.screen.height,
          user_agent: navigator.userAgent,
        },
      });
      setSessionId(sessionData.id);

      // 4. Update UI flags
      setIsSetupPhase(false);
      setIsExamActive(true);
    } catch (err: unknown) {
      console.error(err);
      setError(err instanceof Error ? err.message : "An error occurred starting the assessment.");
      if (document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      }
    }
  };

  // Re-enter Fullscreen button handler
  const handleReenterFullscreen = async () => {
    try {
      if (document.documentElement.requestFullscreen) {
        await document.documentElement.requestFullscreen();
        setIsFullscreenExited(false);
      }
    } catch (err) {
      console.error("Failed to re-enter fullscreen:", err);
    }
  };

  // Connect WebSocket to track coding logs
  const connectWebSocket = (submissionId: number) => {
    if (socketRef.current) {
      socketRef.current.close();
    }

    const wsUrl = `${getWsBase()}/ws/submissions/${submissionId}/?token=${userAccessToken}`;
    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const newLog: LogEntry = {
        id: Math.random().toString(),
        message: "",
        type: "info",
      };

      if (data.type === "connected") {
        newLog.message = `[SYSTEM] Connected to execution agent for Submission #${submissionId}`;
        newLog.type = "info";
        setLogs((prev) => [...prev, newLog]);
      } else if (data.type === "status_changed") {
        newLog.message = `[TASK] Status updated: ${data.status.toUpperCase()}`;
        if (data.score !== null && data.score !== undefined) {
          newLog.message += ` | Total Score: ${data.score}`;
        }
        newLog.type = data.status === "failed" ? "error" : "info";
        setSubmissionStatus(data.status);
        setLogs((prev) => [...prev, newLog]);
      } else if (data.type === "log_appended") {
        const entry = data.entry;
        newLog.message = `[CASE #${entry.test_case_index + 1}] ${entry.passed ? "PASS" : "FAIL"}`;
        newLog.type = entry.passed ? "success" : "error";
        
        let details = `Exit Code: ${entry.exit_code} | Timed Out: ${entry.timed_out ? "Yes" : "No"}`;
        if (entry.stdout_preview) {
          details += `\nStdout:\n${entry.stdout_preview}`;
        }
        if (entry.stderr_preview) {
          details += `\nStderr:\n${entry.stderr_preview}`;
        }
        newLog.details = details;
        newLog.stdoutUrl = entry.stdout_url;
        newLog.stderrUrl = entry.stderr_url;
        setLogs((prev) => [...prev, newLog]);
      } else if (data.type === "evaluation_complete") {
        newLog.message = `[COMPLETE] Evaluation finalized: Passed ${data.passed}/${data.total_cases} test cases. Final Score: ${data.score}`;
        newLog.type = data.passed === data.total_cases ? "success" : "warning";
        setLogs((prev) => [...prev, newLog]);
        ws.close();
      }
    };

    ws.onerror = () => {
      setLogs((prev) => [
        ...prev,
        {
          id: Math.random().toString(),
          message: "[WS ERROR] Live connection socket dropped.",
          type: "error",
        },
      ]);
    };
  };

  // Submit Code solution
  const submitCode = async () => {
    if (!selectedProblem || !assessment) return;

    setSubmissionStatus("Submitting...");
    setLogs([
      {
        id: "init",
        message: `Initializing sandboxed execution environment...`,
        type: "info",
      },
    ]);

    try {
      const res = await authFetch(
        `/api/v1/assessments/problems/${selectedProblem.id}/submissions/`,
        {
          method: "POST",
          body: JSON.stringify({ source_code: code }),
        }
      );

      if (res.status === 429) {
        setSubmissionStatus("Rate Limited");
        setLogs((prev) => [
          ...prev,
          {
            id: "error-429",
            message: "Too many submissions. Please wait a moment before trying again.",
            type: "warning",
          },
        ]);
        return;
      }

      if (!res.ok) {
        throw new Error("Failed to queue submission");
      }

      const data = await res.json();
      setSubmissionStatus("Queued");
      setLogs((prev) => [
        ...prev,
        {
          id: "queued",
          message: `Submission #${data.id} successfully queued. Dispatching worker.`,
          type: "info",
        },
      ]);
      
      connectWebSocket(data.id);
    } catch (err: unknown) {
      setSubmissionStatus("Failed");
      setLogs((prev) => [
        ...prev,
        {
          id: "error-submit",
          message: err instanceof Error ? err.message : "Failed to submit code.",
          type: "error",
        },
      ]);
    }
  };

  // Finish assessment
  const finishAssessment = async (isAutoSubmit = false) => {
    if (!assessment) return;

    if (!isAutoSubmit) {
      const confirmFinish = confirm("Are you sure you want to finish the assessment? You will not be able to change your code solutions.");
      if (!confirmFinish) return;
    }

    try {
      // 1. Submit finish assessment on backend
      const res = await authFetch(`/api/v1/assessments/${assessment.id}/finish/`, {
        method: "POST",
        body: JSON.stringify({ token }),
      });
      if (!res.ok) {
        throw new Error("Failed to finalize assessment on backend.");
      }

      // 2. Submit close session on proctoring backend
      if (sessionId) {
        await authFetch("/api/v1/proctoring/session/end/", {
          method: "POST",
          body: JSON.stringify({ session_id: sessionId }),
        }).catch((e) => console.error("Error closing proctoring session:", e));
      }

      // 3. Stop streams
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (screenStreamRef.current) {
        screenStreamRef.current.getTracks().forEach((track) => track.stop());
      }

      // 4. Exit Fullscreen
      if (document.fullscreenElement && document.exitFullscreen) {
        await document.exitFullscreen().catch(() => {});
      }

      setIsExamActive(false);
      setIsCompleted(true);
    } catch (err: unknown) {
      console.error(err);
      setError("Failed to finalize assessment. Please check your network connection.");
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  // Loader screen
  if (loading) {
    return (
      <div className={styles.container}>
        <div style={{ textAlign: "center" }}>
          <div className="animate-spin" style={{ width: "40px", height: "40px", border: "3px solid var(--border-color)", borderTopColor: "var(--accent-primary)", borderRadius: "50%", margin: "0 auto 16px" }} />
          <p style={{ color: "var(--text-muted)", fontSize: "14px" }}>Retrieving assessment profile...</p>
        </div>
      </div>
    );
  }

  // Setup/Permission waiting room phase
  if (isSetupPhase) {
    return (
      <div className={styles.container}>
        <div className={`${styles.waitingRoom} glass-panel animate-fade-in`}>
          <div>
            <h1 className={styles.waitingTitle}>Secure Assessment Setup</h1>
            <p className={styles.waitingSubtitle}>
              {assessment?.organization.toUpperCase()} • {assessment?.title}
            </p>
          </div>

          {error && <div className={styles.errorMessage}>{error}</div>}

          <div className={styles.rulesSection}>
            <h2 className={styles.rulesTitle}>Assessment Rules & Anti-Cheating Policy</h2>
            <ul className={styles.rulesList}>
              <li>Camera & microphone access must be enabled and active for the entire duration.</li>
              <li>Compulsory entire screen sharing must be active. Sharing window/tab is blocked.</li>
              <li>Exiting fullscreen or switching browser tabs/windows will trigger a proctoring violation.</li>
              <li>Right-click, copy, cut, and paste features are fully disabled.</li>
              <li>Reaching 2 warnings will result in automated test submission.</li>
            </ul>
          </div>

          <div className={styles.setupGrid}>
            {/* Status Checklist */}
            <div className={styles.setupPanel}>
              <div className={styles.setupStatus}>
                <div className={styles.statusItem}>
                  <span className={styles.statusLabel}>Camera Permission</span>
                  <span className={`${styles.statusBadge} ${proctoringState.isCameraActive ? styles.statusSuccess : styles.statusPending}`}>
                    {proctoringState.isCameraActive ? "Active" : "Pending"}
                  </span>
                </div>
                <div className={styles.statusItem}>
                  <span className={styles.statusLabel}>Microphone Permission</span>
                  <span className={`${styles.statusBadge} ${proctoringState.isMicActive ? styles.statusSuccess : styles.statusPending}`}>
                    {proctoringState.isMicActive ? "Active" : "Pending"}
                  </span>
                </div>
                <div className={styles.statusItem}>
                  <span className={styles.statusLabel}>Screen Sharing (Monitor)</span>
                  <span className={`${styles.statusBadge} ${proctoringState.isScreenSharingActive ? styles.statusSuccess : styles.statusPending}`}>
                    {proctoringState.isScreenSharingActive ? "Granted" : "Pending"}
                  </span>
                </div>
                <div className={styles.statusItem}>
                  <span className={styles.statusLabel}>ML Proctoring Guard</span>
                  <span className={`${styles.statusBadge} ${modelsLoaded ? styles.statusSuccess : styles.statusPending}`}>
                    {modelsLoaded ? "Ready" : "Initializing..."}
                  </span>
                </div>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                <button className={styles.actionBtn} onClick={startCameraAndMic}>
                  Grant Camera & Mic Access
                </button>
                <button className={styles.actionBtn} onClick={startScreenShare}>
                  Grant Screen Share (Entire Screen)
                </button>
              </div>
            </div>

            {/* Camera Preview */}
            <div className={styles.videoPreview}>
              {proctoringState.isCameraActive ? (
                <video ref={setupVideoRef} autoPlay playsInline muted className={styles.previewStream} />
              ) : (
                <div className={styles.noPreview}>
                  Webcam preview will render here once permissions are granted.
                </div>
              )}
            </div>
          </div>

          {/* Terms checkbox */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px", justifyContent: "center" }}>
            <input
              type="checkbox"
              id="terms"
              checked={termsAccepted}
              onChange={(e) => setTermsAccepted(e.target.checked)}
              style={{ cursor: "pointer" }}
            />
            <label htmlFor="terms" style={{ fontSize: "13px", color: "var(--text-muted)", cursor: "pointer", userSelect: "none" }}>
              I agree to the proctoring policies and promise to work with integrity.
            </label>
          </div>

          <button
            className={styles.startBtn}
            onClick={handleStartAssessment}
            disabled={
              !proctoringState.isCameraActive ||
              !proctoringState.isMicActive ||
              !proctoringState.isScreenSharingActive ||
              !termsAccepted ||
              !modelsLoaded
            }
          >
            {modelsLoaded ? "Start Proctored Assessment" : "Initializing ML Guards..."}
          </button>
        </div>
      </div>
    );
  }

  // Final Summary/Completed screen
  if (isCompleted) {
    return (
      <div className={styles.container}>
        <div className={`${styles.statusCard} glass-panel animate-fade-in`}>
          <div className={styles.statusIcon}>
            {error ? "Error" : "Active"}
          </div>
          <h1 className={styles.waitingTitle}>
            {error ? "Assessment Terminated" : "Assessment Completed"}
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "14px", lineHeight: "1.5" }}>
            {error 
              ? error 
              : "Thank you for completing the assessment! Your code and proctoring telemetry logs have been submitted successfully. The recruiter will review your profile shortly."
            }
          </p>
          <button className={styles.reenterBtn} style={{ background: "var(--accent-primary)", marginTop: "16px" }} onClick={() => router.push("/")}>
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // Active Exam Workspace
  return (
    <div className={styles.workspaceLayout}>
      {/* Workspace Header */}
      <header className={styles.workspaceHeader}>
        <div className={styles.headerLogo}>
          <span style={{ color: "var(--color-error)" }}>Proctored Environment</span>
          <span style={{ fontSize: "11px", opacity: 0.4 }}>|</span>
          <span style={{ fontSize: "12px", opacity: 0.8 }}>{assessment?.title}</span>
        </div>

        <div className={styles.headerStats}>
          {/* Violation warning badge */}
          <div className={styles.violationCount}>
            <span>Warnings:</span>
            <span>{warningCount} / 2</span>
          </div>

          {/* Timer Countdown */}
          <div className={styles.timer}>
            <span>⏱️ Time Remaining:</span>
            <span>{formatTime(timeLeft)}</span>
          </div>

          <button className={styles.finishBtn} onClick={() => finishAssessment(false)}>
            Submit & Finish
          </button>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <main className={styles.workspaceMain}>
        {/* Left Side: Problem list */}
        <section className={`${styles.sidebarPanel} glass-panel`}>
          <h2 className={styles.panelTitle}>Challenges</h2>
          <div className={styles.sidebarContent}>
            <ul className={styles.problemsList}>
              {assessment?.problems?.map((prob) => (
                <li
                  key={prob.id}
                  className={`${styles.problemItem} ${
                    selectedProblem?.id === prob.id ? styles.problemItemActive : ""
                  }`}
                  onClick={() => setSelectedProblem(prob)}
                >
                  <div className={styles.problemItemHeader}>
                    <span className={styles.problemItemName}>{prob.title}</span>
                    <span className={styles.problemItemLang}>{prob.language}</span>
                  </div>
                  <span className={styles.problemItemPoints}>Max Score: {prob.max_score} pts</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Center: Monaco Editor & Prompt */}
        <section className={`${styles.editorPanel} glass-panel`}>
          <div className={styles.editorContent}>
            {selectedProblem && (
              <>
                <div className={styles.promptCard}>
                  <h3 style={{ fontSize: "15px", marginBottom: "6px", color: "#fff" }}>
                    {selectedProblem.title}
                  </h3>
                  <pre className={styles.promptText}>{selectedProblem.prompt}</pre>
                  <div style={{ marginTop: "8px", display: "flex", gap: "16px", fontSize: "11px", opacity: 0.5 }}>
                    <span>Timeout: {selectedProblem.time_limit_ms}ms</span>
                    <span>Memory: {selectedProblem.memory_limit_mb}MB</span>
                  </div>
                </div>

                <div className={styles.editorWrapper}>
                  <Editor
                    height="100%"
                    language={selectedProblem.language}
                    theme="vs-dark"
                    value={code}
                    onChange={(val) => setCode(val || "")}
                    options={{
                      fontSize: 13,
                      fontFamily: "var(--font-mono)",
                      minimap: { enabled: false },
                      automaticLayout: true,
                      contextmenu: false,
                    }}
                  />
                </div>

                <div className={styles.editorControls}>
                  <div className={styles.languageLabel}>
                    <span>Mode:</span>
                    <span className={styles.problemItemLang}>{selectedProblem.language}</span>
                  </div>

                  <button
                    className={styles.submitBtn}
                    onClick={submitCode}
                    disabled={timeLeft <= 0 || submissionStatus === "Submitting..."}
                  >
                    <span>Submit Code</span>
                  </button>
                </div>
              </>
            )}
          </div>
        </section>

        {/* Right Side: Execution Console */}
        <section className={`${styles.logsPanel} glass-panel`}>
          <h2 className={styles.panelTitle}>
            <span>Run Logs Console</span>
            {submissionStatus && (
              <span className={`${styles.statusBadge} ${submissionStatus === "queued" ? styles.statusPending : styles.statusSuccess}`}>
                {submissionStatus}
              </span>
            )}
          </h2>

          <div className={styles.logsContent}>
            <div className={styles.logTerminal}>
              {logs.length === 0 ? (
                <div style={{ opacity: 0.4 }}>No logs compiled. Sandboxed test case updates stream here.</div>
              ) : (
                logs.map((log) => (
                  <div key={log.id} className={styles.logLine}>
                    <span className={log.type === "success" ? styles.logSuccess : log.type === "error" ? styles.logError : log.type === "warning" ? styles.logWarning : styles.logInfo}>
                      {log.message}
                    </span>
                    {log.details && <pre className={styles.logDetails}>{log.details}</pre>}
                    {(log.stdoutUrl || log.stderrUrl) && (
                      <div style={{ display: "flex", gap: "8px", marginTop: "4px" }}>
                        {log.stdoutUrl && (
                          <a href={log.stdoutUrl} target="_blank" rel="noreferrer" className={styles.logDetails}>
                            stdout
                          </a>
                        )}
                        {log.stderrUrl && (
                          <a href={log.stderrUrl} target="_blank" rel="noreferrer" className={styles.logDetails}>
                            stderr
                          </a>
                        )}
                      </div>
                    )}
                  </div>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          </div>
        </section>
      </main>

      {/* Floating corner Camera Feed */}
      <div className={styles.cameraOverlay}>
        <video ref={workspaceVideoRef} autoPlay playsInline muted className={styles.cameraStream} />
      </div>

      {/* Blocking Fullscreen exit overlay */}
      {isFullscreenExited && (
        <div className={styles.fullscreenBlocker}>
          <div className={`${styles.warningModal} glass-panel`}>
            <div className={styles.warningIcon}>!</div>
            <h2 className={styles.warningTitle}>FULLSCREEN MODE REQUIRED</h2>
            <p className={styles.warningText}>
              You have exited fullscreen mode. Exiting fullscreen is a proctoring violation. 
              Please return to fullscreen immediately to avoid losing access to this assessment.
            </p>
            <button className={styles.reenterBtn} onClick={handleReenterFullscreen}>
              Return to Fullscreen
            </button>
          </div>
        </div>
      )}

      {/* Dismissible warning notification overlay */}
      {warningMessage && (
        <div className={styles.modalOverlay} onClick={() => setWarningMessage(null)}>
          <div className={`${styles.warningModal} glass-panel`} onClick={(e) => e.stopPropagation()}>
            <div className={styles.warningIcon} style={{ color: "var(--color-warning)" }}>!</div>
            <h2 className={styles.warningTitle}>PROCTORING WARNING</h2>
            <p className={styles.warningText}>{warningMessage}</p>
            <button className={styles.reenterBtn} style={{ background: "var(--color-warning)" }} onClick={() => setWarningMessage(null)}>
              Acknowledge & Continue
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Refactor: Refactor variable names for better readability.

// Refactor: Align with project code quality guidelines.

// Refactor: Enhance component rendering performance.

// Refactor: Align with project code quality guidelines.

// Refactor: Optimize query performance and database indexing.

// Refactor: Fix minor edge cases in calculation functions.

// Refactor: Add typing hints and documentation docstrings.
