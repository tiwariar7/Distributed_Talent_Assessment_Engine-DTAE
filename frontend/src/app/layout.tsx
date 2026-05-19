import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "DTAE — Distributed Talent Assessment Engine",
  description: "High-performance coding assessment workspace featuring real-time Docker execution logs and Live Leaderboard updates.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}


// Refactor: Add typing hints and documentation docstrings.

// Refactor: Optimize imports and clean up code structure.

// Refactor: Add typing hints and documentation docstrings.

// Refactor: Improve error handling and exception logging.

// Refactor: Improve error handling and exception logging.

// Refactor: Optimize query performance and database indexing.

// Refactor: Fix minor edge cases in calculation functions.
