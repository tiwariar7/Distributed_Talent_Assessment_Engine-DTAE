/**
 * Stateless Client-side JWT utilities for DTAE.
 * Decodes tokens for UI gating and role checks without keeping global state.
 */

export interface MembershipClaim {
  org_slug: string;
  org_name: string;
  role_code: string;
}

export interface DecodedToken {
  user_id: number;
  email: string;
  first_name: string;
  last_name: string;
  memberships: MembershipClaim[];
  exp: number;
  iat: number;
  jti: string;
}

/**
 * Decode a JWT payload without signature verification.
 * Returns null if the token is malformed or expired.
 */
export function decodeToken(token: string | null): DecodedToken | null {
  if (!token) return null;

  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;

    const payload = JSON.parse(atob(parts[1].replace(/-/g, "+").replace(/_/g, "/")));

    // Check expiry
    if (payload.exp && payload.exp * 1000 < Date.now()) {
      return null;
    }

    return {
      user_id: payload.user_id,
      email: payload.email ?? "",
      first_name: payload.first_name ?? "",
      last_name: payload.last_name ?? "",
      memberships: payload.memberships ?? [],
      exp: payload.exp,
      iat: payload.iat,
      jti: payload.jti,
    };
  } catch {
    return null;
  }
}

/** Check if the token has a specific role in any organization. */
export function hasRole(token: string | null, roleCode: string): boolean {
  const decoded = decodeToken(token);
  if (!decoded) return false;
  return decoded.memberships.some((m) => m.role_code === roleCode);
}

/** Check if token belongs to a recruiter. */
export function isRecruiter(token: string | null): boolean {
  return hasRole(token, "recruiter");
}

/** Check if token belongs to a candidate. */
export function isCandidate(token: string | null): boolean {
  return hasRole(token, "candidate");
}

/** Get user's display name from token. */
export function getUserDisplayName(token: string | null): string {
  const decoded = decodeToken(token);
  if (!decoded) return "";
  const name = `${decoded.first_name} ${decoded.last_name}`.trim();
  return name || decoded.email;
}

/** Get user's email from token. */
export function getUserEmail(token: string | null): string {
  return decodeToken(token)?.email ?? "";
}

/** Get all organizations from token. */
export function getUserOrganizations(token: string | null): MembershipClaim[] {
  return decodeToken(token)?.memberships ?? [];
}

/** Check if a token is valid (not expired). */
export function isTokenValid(token: string | null): boolean {
  return decodeToken(token) !== null;
}

// Refactor: Optimize query performance and database indexing.

// Refactor: Align with project code quality guidelines.

// Refactor: Optimize query performance and database indexing.

// Refactor: Align with project code quality guidelines.

// Refactor: Refactor variable names for better readability.
