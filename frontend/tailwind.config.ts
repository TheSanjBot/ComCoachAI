import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./hooks/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        surface: {
          DEFAULT: "hsl(var(--surface))",
          foreground: "hsl(var(--surface-foreground))"
        },
        bitcoin: "hsl(var(--bitcoin))",
        burnt: "hsl(var(--burnt))",
        gold: "hsl(var(--gold))",
        void: "hsl(var(--void))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))"
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))"
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))"
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))"
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))"
        }
      },
      fontFamily: {
        heading: ["var(--font-heading)", "sans-serif"],
        body: ["var(--font-body)", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"]
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)"
      },
      boxShadow: {
        halo: "0 0 30px -8px rgba(247, 147, 26, 0.35)",
        "orange-glow": "0 0 20px -5px rgba(234, 88, 12, 0.5)",
        "orange-glow-strong": "0 0 30px -5px rgba(247, 147, 26, 0.6)",
        "orange-glow-subtle": "0 0 30px -10px rgba(247, 147, 26, 0.2)",
        "gold-glow": "0 0 20px rgba(255, 214, 0, 0.28)",
        "panel-glow": "0 0 50px -10px rgba(247, 147, 26, 0.12)"
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-20px)" }
        },
        "orbit-reverse": {
          from: { transform: "rotate(360deg)" },
          to: { transform: "rotate(0deg)" }
        }
      },
      animation: {
        float: "float 8s ease-in-out infinite",
        "orbit-reverse": "orbit-reverse 15s linear infinite"
      }
    }
  },
  plugins: []
};

export default config;
