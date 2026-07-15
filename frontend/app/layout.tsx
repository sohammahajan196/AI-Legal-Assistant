/**
 * Root layout — Source Serif 4 for titles, Manrope + IBM Plex Mono for UI.
 */
import "./globals.css";
import type { Metadata } from "next";
import {
  IBM_Plex_Mono,
  Manrope,
  Source_Serif_4,
} from "next/font/google";

import { TooltipProvider } from "@/components/ui/tooltip";

const sourceSerif = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["400", "500", "600"],
  style: ["normal", "italic"],
  display: "swap",
});

const manrope = Manrope({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Nyāya — AI Legal Assistant",
  description:
    "Explainable, citation-grounded answers to Indian legal questions.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${sourceSerif.variable} ${manrope.variable} ${plexMono.variable}`}
    >
      <body className="min-h-screen bg-shell font-sans text-ink antialiased">
        <TooltipProvider delayDuration={300}>{children}</TooltipProvider>
      </body>
    </html>
  );
}
