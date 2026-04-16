import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
      {
        source: "/health/:path*",
        destination: "http://localhost:8000/health/:path*",
      },
    ];
  },
};

export default nextConfig;

// Refactor: Fix minor edge cases in calculation functions.

// Refactor: Update validation checks and constraints.

// Refactor: Enhance component rendering performance.

// Refactor: Optimize query performance and database indexing.
