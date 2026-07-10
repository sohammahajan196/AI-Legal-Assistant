/**
 * Root layout for the AI Legal Assistant chat UI.
 *
 * Intended to host the always-visible DisclaimerBanner alongside page
 * content. See STRUCTURE.md and TASKS.md T43/T45.
 */
import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Legal Assistant",
  description:
    "Explainable, citation-grounded answers to Indian legal questions.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {/* TODO: render <DisclaimerBanner /> here once implemented (T45) */}
        {children}
      </body>
    </html>
  );
}
