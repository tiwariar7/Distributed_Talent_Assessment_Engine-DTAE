/**
 * Centralized API client for DTAE.
 * Completely stateless: token state is injected via registerTokenGetter.
 */

// Global stateless hooks for token extraction & callbacks
let getAccessTokenFn: () => string | null = () => null;
let triggerLogoutFn: () => void = () => {};

export function registerTokenGetter(fn: () => string | null) {
  getAccessTokenFn = fn;
}

export function registerLogoutHandler(fn: () => void) {
  triggerLogoutFn = fn;
}

/** Resolve API base URL. Dev falls back to relative, production uses env */
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "";

/** Resolve WebSocket base URL routing port 3000 -> 8000 on development */
export const getWsBase = (): string => {
  if (typeof window === "undefined") return "ws://localhost:8000";
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  
  // Local development redirect from port 3000 to port 8000
  if (window.location.port === "3000") {
    return `ws://localhost:8000`;
  }
  
  return `${protocol}//${window.location.host}`;
};

export interface NormalizedError {
  message: string;
  fieldErrors?: Record<string, string[]>;
  statusCode?: number;
}

/**
 * Standard fetch wrapper that injects Bearer token.
 * Triggers logout callback on 401.
 */
export async function authFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getAccessTokenFn();
  const fullUrl = url.startsWith("http") ? url : `${API_BASE}${url}`;

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Inject CSRF header if running in browser and cookie is available
  if (typeof document !== "undefined") {
    const csrfMatch = document.cookie.match(/csrftoken=([^;]+)/);
    if (csrfMatch) {
      headers["X-CSRFToken"] = csrfMatch[1];
    }
  }

  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = headers["Content-Type"] ?? "application/json";
  }

  const response = await fetch(fullUrl, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    triggerLogoutFn();
  }

  return response;
}

/** Normalized parser throwing detailed NormalizedError */
export async function apiFetch<T = unknown>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  try {
    const response = await authFetch(url, options);

    if (!response.ok) {
      let errorData: any = {};
      try {
        errorData = await response.json();
      } catch {
        // Fallback for non-JSON responses
      }

      const normalized: NormalizedError = {
        message: errorData.detail || errorData.error || errorData.message || `Request failed: ${response.statusText}`,
        fieldErrors: errorData.errors || (errorData.detail ? undefined : errorData),
        statusCode: response.status,
      };
      throw normalized;
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  } catch (err: any) {
    if (err.message && !err.statusCode) {
      // General network error
      const normalized: NormalizedError = {
        message: err.message || "Network request failed. Please check your connection.",
      };
      throw normalized;
    }
    throw err;
  }
}

export async function apiPost<T = unknown>(
  url: string,
  body: Record<string, unknown>
): Promise<T> {
  return apiFetch<T>(url, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function apiPut<T = unknown>(
  url: string,
  body: Record<string, unknown>
): Promise<T> {
  return apiFetch<T>(url, {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export async function apiDelete<T = unknown>(url: string): Promise<T> {
  return apiFetch<T>(url, { method: "DELETE" });
}

// Refactor: Optimize query performance and database indexing.
