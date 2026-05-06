/**
 * mlModelCache.ts
 *
 * Module-level singleton cache for heavy ML models (COCO-SSD + Tesseract OCR).
 * Models are loaded ONCE per browser session and reused across page navigations.
 *
 * Pre-warm on the invitations page so they are ready by the time
 * the candidate clicks "Start Assessment".
 */

"use client";

// Singleton state — persists across React re-renders and route changes.
let initPromise: Promise<void> | null = null;
let cocoModel: any = null;
let tesseractWorker: any = null;
let loaded = false;
let loadError: string | null = null;

/** Load a CDN script exactly once — idempotent. */
function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (typeof window === "undefined") return resolve();
    if (document.querySelector(`script[src="${src}"]`)) return resolve();
    const s = document.createElement("script");
    s.src = src;
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error(`Script load failed: ${src}`));
    document.body.appendChild(s);
  });
}

/**
 * Trigger model pre-loading. Safe to call multiple times — runs only once.
 * Returns the same Promise every subsequent call.
 */
export function preloadMLModels(): Promise<void> {
  if (initPromise) return initPromise;

  initPromise = (async () => {
    try {
      console.log("[MLCache] Starting ML model pre-load...");

      // Load CDN scripts in parallel where possible
      await loadScript("https://cdn.jsdelivr.net/npm/@tensorflow/tfjs");
      await loadScript("https://cdn.jsdelivr.net/npm/@tensorflow-models/coco-ssd");
      await loadScript("https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js");

      // Initialise models in parallel
      const [coco, tesseract] = await Promise.all([
        // @ts-ignore
        (window as any).cocoSsd.load(),
        // @ts-ignore
        (window as any).Tesseract.createWorker("eng"),
      ]);

      cocoModel = coco;
      tesseractWorker = tesseract;
      loaded = true;
      loadError = null;
      console.log("[MLCache] COCO-SSD & Tesseract fully loaded and cached.");
    } catch (err: any) {
      loadError = err?.message || "Unknown ML load error";
      console.error("[MLCache] ML model pre-load failed:", err);
      // Reset so the next call can retry
      initPromise = null;
    }
  })();

  return initPromise;
}

/** Returns cached COCO-SSD model (null if not loaded yet). */
export function getCachedCocoModel(): any {
  return cocoModel;
}

/** Returns cached Tesseract worker (null if not loaded yet). */
export function getCachedTesseractWorker(): any {
  return tesseractWorker;
}

/** True once both models are successfully initialised. */
export function areModelsLoaded(): boolean {
  return loaded;
}

/** Last load error message, or null. */
export function getModelLoadError(): string | null {
  return loadError;
}

/**
 * Terminate Tesseract worker and reset cache.
 * Call this when the user logs out or the session ends permanently.
 */
export function teardownMLModels(): void {
  if (tesseractWorker) {
    tesseractWorker.terminate().catch(() => {});
  }
  cocoModel = null;
  tesseractWorker = null;
  loaded = false;
  loadError = null;
  initPromise = null;
  console.log("[MLCache] Models torn down.");
}

// Refactor: Refactor variable names for better readability.

// Refactor: Enhance component rendering performance.

// Refactor: Update validation checks and constraints.

// Refactor: Improve responsive styles and layouts.

// Refactor: Refactor variable names for better readability.

// Refactor: Optimize imports and clean up code structure.

// Refactor: Optimize imports and clean up code structure.

// Refactor: Optimize imports and clean up code structure.

// Refactor: Optimize imports and clean up code structure.
