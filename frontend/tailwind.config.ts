/**
 * Tailwind CSS configuration — minimal dark graphite theme.
 */
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        display: [
          "var(--font-display)",
          "Source Serif 4",
          "Iowan Old Style",
          "Georgia",
          "serif",
        ],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        shell: "var(--bg-shell)",
        elevated: "var(--bg-elevated)",
        surface: "var(--bg-surface)",
        "surface-soft": "var(--bg-surface-soft)",
        ink: {
          DEFAULT: "var(--ink-primary)",
          muted: "var(--ink-muted)",
          cream: "var(--ink-on-cream)",
          "cream-muted": "var(--ink-on-cream-muted)",
        },
        amber: "var(--accent-amber)",
        wine: "var(--accent-wine)",
        /* Back-compat aliases used across older component classes */
        burgundy: "var(--accent-wine)",
        brass: "var(--accent-amber)",
        warm: "var(--border-cream)",
        parchment: "var(--bg-shell)",
        disclaimer: "var(--disclaimer-bg)",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [],
};

export default config;
