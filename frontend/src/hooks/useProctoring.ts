"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { getWsBase } from "../services/api";
import {
  preloadMLModels,
  getCachedCocoModel,
  getCachedTesseractWorker,
  areModelsLoaded,
} from "../app/lib/mlModelCache";

export interface ProctoringState {
  isCameraActive: boolean;
  isMicActive: boolean;
  isScreenSharingActive: boolean;
  violationCount: number;
  warningsCount: number;
  autoSubmitted: boolean;
  error: string | null;
}

interface UseProctoringOptions {
  invitationId: string;
  token: string;
  maxWarnings: number;
  isExamActive: boolean;
  onWarningIssued: (violationType: string, count: number) => void;
  onAutoSubmitted: (reason: string) => void;
}

export function useProctoring({
  invitationId,
  token,
  maxWarnings,
  isExamActive,
  onWarningIssued,
  onAutoSubmitted,
}: UseProctoringOptions) {
  const [state, setState] = useState<ProctoringState>({
    isCameraActive: false,
    isMicActive: false,
    isScreenSharingActive: false,
    violationCount: 0,
    warningsCount: 0,
    autoSubmitted: false,
    error: null,
  });

  const [modelsLoaded, setModelsLoaded] = useState<boolean>(areModelsLoaded);

  const cocoModelRef = useRef<any>(getCachedCocoModel());
  const tesseractWorkerRef = useRef<any>(getCachedTesseractWorker());

  const wsRef = useRef<WebSocket | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const screenStreamRef = useRef<MediaStream | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastActiveRef = useRef<number>(Date.now());

  const sendTelemetry = useCallback((eventType: string, metadata: Record<string, unknown> = {}) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          event_type: eventType,
          metadata: {
            ...metadata,
            timestamp: new Date().toISOString(),
          },
        })
      );
    }
  }, []);

  useEffect(() => {
    if (areModelsLoaded()) {
      cocoModelRef.current = getCachedCocoModel();
      tesseractWorkerRef.current = getCachedTesseractWorker();
      setModelsLoaded(true);
      return;
    }

    preloadMLModels();

    const poll = setInterval(() => {
      if (areModelsLoaded()) {
        cocoModelRef.current = getCachedCocoModel();
        tesseractWorkerRef.current = getCachedTesseractWorker();
        setModelsLoaded(true);
        clearInterval(poll);
        console.log("[useProctoring] ML models ready (from cache).");
      }
    }, 500);

    return () => clearInterval(poll);
  }, []);

  const startCameraAndMic = useCallback(async () => {
    try {
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 320, height: 240, frameRate: 15 },
        audio: true,
      });

      mediaStreamRef.current = stream;

      stream.getTracks().forEach((track) => {
        track.onended = () => {
          if (track.kind === "video") {
            setState((prev) => ({ ...prev, isCameraActive: false }));
            sendTelemetry("camera_blocked", { reason: "camera track ended" });
          } else {
            setState((prev) => ({ ...prev, isMicActive: false }));
            sendTelemetry("mic_blocked", { reason: "mic track ended" });
          }
        };
      });

      setState((prev) => ({
        ...prev,
        isCameraActive: true,
        isMicActive: true,
        error: null,
      }));

      return stream;
    } catch (err: unknown) {
      console.error("Camera/Mic permissions failed:", err);
      setState((prev) => ({
        ...prev,
        isCameraActive: false,
        isMicActive: false,
        error: "Camera and microphone access are required for this assessment.",
      }));
      throw err;
    }
  }, [sendTelemetry]);

  const startScreenShare = useCallback(async () => {
    try {
      if (screenStreamRef.current) {
        screenStreamRef.current.getTracks().forEach((track) => track.stop());
      }

      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: {
          displaySurface: "monitor",
        } as unknown as MediaTrackConstraints,
        audio: false,
      });

      const videoTrack = stream.getVideoTracks()[0];
      const settings = videoTrack.getSettings();
      
      if (settings.displaySurface && settings.displaySurface !== "monitor") {
        stream.getTracks().forEach((track) => track.stop());
        setState((prev) => ({ ...prev, isScreenSharingActive: false }));
        throw new Error("You must share your entire screen/monitor. Sharing a window or tab is not allowed.");
      }

      screenStreamRef.current = stream;

      videoTrack.onended = () => {
        setState((prev) => ({ ...prev, isScreenSharingActive: false }));
        sendTelemetry("fullscreen_exit", { reason: "screen share track ended" });
      };

      setState((prev) => ({
        ...prev,
        isScreenSharingActive: true,
        error: null,
      }));

      return stream;
    } catch (err: unknown) {
      console.error("Screen sharing failed:", err);
      setState((prev) => ({
        ...prev,
        isScreenSharingActive: false,
        error: (err instanceof Error ? err.message : String(err)) || "Entire screen sharing is required to start this assessment.",
      }));
      throw err;
    }
  }, [sendTelemetry]);

  const checkClipboard = useCallback(async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        sendTelemetry("copy_paste", {
          action: "clipboard_read",
          length: text.length,
          preview: text.substring(0, 100),
        });
      }
    } catch (e) {
      // Permission denied
    }
  }, [sendTelemetry]);

  useEffect(() => {
    if (!invitationId || !token) return;

    const wsUrl = `${getWsBase()}/ws/proctoring/${invitationId}/?token=${token}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("Proctoring WebSocket connected.");
      heartbeatIntervalRef.current = setInterval(() => {
        sendTelemetry("ping");
      }, 30000);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.event_type === "pong") {
        return;
      }

      if (data.event_type === "warning_issued") {
        setState((prev) => ({
          ...prev,
          violationCount: data.violation_count,
          warningsCount: data.violation_count,
        }));
        onWarningIssued(data.violation_type, data.violation_count);
      } else if (data.event_type === "auto_submit") {
        setState((prev) => ({
          ...prev,
          violationCount: data.violation_count,
          warningsCount: data.violation_count,
          autoSubmitted: true,
        }));
        onAutoSubmitted("Violation count exceeded the maximum limit.");
      }
    };

    ws.onerror = (err) => {
      console.error("Proctoring WS error:", err);
    };

    ws.onclose = () => {
      console.log("Proctoring WebSocket closed.");
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }
    };

    return () => {
      ws.close();
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }
    };
  }, [invitationId, token, sendTelemetry, onWarningIssued, onAutoSubmitted]);

  useEffect(() => {
    if (!isExamActive || !state.isCameraActive || !modelsLoaded || !cocoModelRef.current) return;

    let timer: NodeJS.Timeout;
    
    const detectObjects = async () => {
      try {
        const videoElement = document.querySelector("video[class*='cameraStream']") as HTMLVideoElement;
        if (videoElement && videoElement.readyState >= 3) {
          const predictions = await cocoModelRef.current.detect(videoElement);
          
          let cellPhoneCount = 0;
          let personCount = 0;

          predictions.forEach((p: any) => {
            if (p.class === "cell phone" && p.score > 0.6) {
              cellPhoneCount++;
            }
            if (p.class === "person" && p.score > 0.5) {
              personCount++;
            }
          });

          if (cellPhoneCount > 0) {
            sendTelemetry("phone_detected", { confidence: predictions.find((p: any) => p.class === "cell phone")?.score });
          }

          if (personCount > 1) {
            sendTelemetry("multiple_faces_detected", { faces_count: personCount });
          } else if (personCount === 0) {
            sendTelemetry("no_face_detected");
          }
        }
      } catch (err) {
        console.error("Proctoring ML detection error:", err);
      }
      
      timer = setTimeout(detectObjects, 2000);
    };

    detectObjects();
    return () => clearTimeout(timer);
  }, [isExamActive, state.isCameraActive, modelsLoaded, sendTelemetry]);

  useEffect(() => {
    if (!isExamActive || !state.isMicActive || !mediaStreamRef.current) return;

    let audioCtx: AudioContext;
    let source: MediaStreamAudioSourceNode;
    let analyser: AnalyserNode;
    let interval: NodeJS.Timeout;

    try {
      audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      source = audioCtx.createMediaStreamSource(mediaStreamRef.current);
      analyser = audioCtx.createAnalyser();
      analyser.fftSize = 512;
      source.connect(analyser);

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      let voiceDetectionCount = 0;

      const checkVoiceActivity = () => {
        analyser.getByteFrequencyData(dataArray);

        let totalEnergy = 0;
        const minIndex = 1;
        const maxIndex = Math.min(35, bufferLength);
        for (let i = minIndex; i < maxIndex; i++) {
          totalEnergy += dataArray[i];
        }
        const averageEnergy = totalEnergy / (maxIndex - minIndex);

        if (averageEnergy > 45) {
          voiceDetectionCount++;
        } else {
          voiceDetectionCount = Math.max(0, voiceDetectionCount - 1);
        }

        if (voiceDetectionCount >= 3) {
          sendTelemetry("voice_activity_detected", { average_energy: averageEnergy });
          voiceDetectionCount = 0;
        }
      };

      interval = setInterval(checkVoiceActivity, 1000);
    } catch (err) {
      console.error("Proctoring voice activity analyzer failure:", err);
    }

    return () => {
      if (interval) clearInterval(interval);
      if (source) source.disconnect();
      if (analyser) analyser.disconnect();
      if (audioCtx) audioCtx.close().catch(() => {});
    };
  }, [isExamActive, state.isMicActive, mediaStreamRef.current, sendTelemetry]);

  useEffect(() => {
    if (!isExamActive || !state.isScreenSharingActive || !modelsLoaded || !tesseractWorkerRef.current || !screenStreamRef.current) return;

    let timer: NodeJS.Timeout;
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    const checkScreenForAI = async () => {
      try {
        const videoTrack = screenStreamRef.current?.getVideoTracks()[0];
        if (videoTrack && videoTrack.readyState === "live" && ctx) {
          const video = document.createElement("video");
          video.srcObject = screenStreamRef.current;
          video.muted = true;
          video.playsInline = true;
          await video.play().catch(() => {});

          if (video.videoWidth > 0 && video.videoHeight > 0) {
            canvas.width = Math.min(video.videoWidth, 1280);
            canvas.height = Math.min(video.videoHeight, 720);
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            const { data: { text } } = await tesseractWorkerRef.current.recognize(canvas);
            
            if (text) {
              const cleanText = text.toLowerCase();
              const aiKeywords = [
                "chatgpt", "openai", "gemini", "claude", 
                "copilot", "perplexity", "deepseek", "phind"
              ];
              
              const promptPatterns = [
                "prompt:", "translate this code", "explain this code", 
                "solve this problem", "write a python function", 
                "leetcode solution"
              ];

              const detectedAI = aiKeywords.find((kw) => cleanText.includes(kw));
              const detectedPrompt = promptPatterns.find((pat) => cleanText.includes(pat));

              if (detectedAI) {
                sendTelemetry("ai_usage_detected", { reason: `AI website signature: ${detectedAI}` });
              } else if (detectedPrompt) {
                sendTelemetry("ai_usage_detected", { reason: `AI prompt signature: ${detectedPrompt}` });
              }
            }
          }
          video.srcObject = null;
          video.remove();
        }
      } catch (err) {
        console.error("Proctoring Screen OCR check failure:", err);
      }

      timer = setTimeout(checkScreenForAI, 6000);
    };

    timer = setTimeout(checkScreenForAI, 5000);
    return () => clearTimeout(timer);
  }, [isExamActive, state.isScreenSharingActive, modelsLoaded, screenStreamRef.current, sendTelemetry]);

  useEffect(() => {
    const handleBlur = () => {
      sendTelemetry("window_blur");
    };

    const handleFocus = () => {
      lastActiveRef.current = Date.now();
      checkClipboard();
    };

    const handleVisibilityChange = () => {
      if (document.hidden) {
        sendTelemetry("tab_switch", { description: "User switched tab or minimized window" });
      }
    };

    const handleFullscreenChange = () => {
      if (!document.fullscreenElement) {
        sendTelemetry("fullscreen_exit");
      }
    };

    const handleResize = () => {
      sendTelemetry("screen_change", {
        viewport_width: window.innerWidth,
        viewport_height: window.innerHeight,
        screen_width: window.screen.width,
        screen_height: window.screen.height,
      });
    };

    const handleContextMenu = (e: MouseEvent) => {
      e.preventDefault();
      sendTelemetry("right_click");
    };

    const handleCopyCutPaste = (e: ClipboardEvent) => {
      e.preventDefault();
      const type = e.type === "paste" ? "paste_attempt" : "copy_attempt";
      
      let clipboardDataText = "";
      if (e.type === "paste" && e.clipboardData) {
        clipboardDataText = e.clipboardData.getData("text") || "";
      }

      sendTelemetry(type, {
        length: clipboardDataText.length,
        preview: clipboardDataText.substring(0, 100),
      });
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      const isCmdOrCtrl = e.ctrlKey || e.metaKey;
      const key = e.key.toLowerCase();

      if (
        (isCmdOrCtrl && ["c", "v", "x", "a", "p"].includes(key)) ||
        (e.shiftKey && e.key === "Insert") ||
        e.key === "PrintScreen"
      ) {
        e.preventDefault();
        const type = ["v", "insert"].includes(key) ? "paste_attempt" : "copy_attempt";
        sendTelemetry(type, { shortcut: e.key });
      }
    };

    window.addEventListener("blur", handleBlur);
    window.addEventListener("focus", handleFocus);
    document.addEventListener("visibilitychange", handleVisibilityChange);
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    window.addEventListener("resize", handleResize);
    document.addEventListener("contextmenu", handleContextMenu);
    document.addEventListener("copy", handleCopyCutPaste);
    document.addEventListener("cut", handleCopyCutPaste);
    document.addEventListener("paste", handleCopyCutPaste);
    document.addEventListener("keydown", handleKeyDown);

    const idleCheck = setInterval(() => {
      if (Date.now() - lastActiveRef.current > 120000) {
        sendTelemetry("idle_timeout", { duration_seconds: 120 });
      }
    }, 30000);

    const updateActivity = () => {
      lastActiveRef.current = Date.now();
    };

    window.addEventListener("mousemove", updateActivity);
    window.addEventListener("keypress", updateActivity);

    return () => {
      window.removeEventListener("blur", handleBlur);
      window.removeEventListener("focus", handleFocus);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
      window.removeEventListener("resize", handleResize);
      document.removeEventListener("contextmenu", handleContextMenu);
      document.removeEventListener("copy", handleCopyCutPaste);
      document.removeEventListener("cut", handleCopyCutPaste);
      document.removeEventListener("paste", handleCopyCutPaste);
      document.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("mousemove", updateActivity);
      window.removeEventListener("keypress", updateActivity);
      clearInterval(idleCheck);
    };
  }, [sendTelemetry, checkClipboard]);

  useEffect(() => {
    return () => {
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (screenStreamRef.current) {
        screenStreamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  return {
    state,
    modelsLoaded,
    mediaStreamRef,
    screenStreamRef,
    startCameraAndMic,
    startScreenShare,
    sendTelemetry,
  };
}

// Refactor: Align with project code quality guidelines.

// Refactor: Improve responsive styles and layouts.

// Refactor: Enhance component rendering performance.

// Refactor: Enhance component rendering performance.
