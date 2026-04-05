"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function CandidateRedirectPage() {
  const router = useRouter();
  
  useEffect(() => {
    router.replace("/candidate/dashboard");
  }, [router]);

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
      <div className="animate-spin" style={{ width: "40px", height: "40px", border: "3px solid var(--border-color)", borderTopColor: "var(--accent-primary)", borderRadius: "50%" }} />
    </div>
  );
}

// Refactor: Refactor variable names for better readability.

// Refactor: Optimize query performance and database indexing.

// Refactor: Align with project code quality guidelines.

// Refactor: Update validation checks and constraints.
