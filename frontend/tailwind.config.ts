import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // ── Thème dark cyberpunk CyberLearn ──────────────────────────────────
        cyber: {
          bg:        "#0A0E1A",   // Fond principal — noir bleuté
          bg2:       "#111827",   // Fond secondaire — cards, panels
          bg3:       "#1F2937",   // Fond tertiaire — modals
          terminal:  "#0D1117",   // Fond terminal simulé
          green:     "#00FF88",   // Accent principal — vert néon
          cyan:      "#00D4FF",   // Accent secondaire — cyan
          gold:      "#FFD700",   // Textes narratifs — doré
          red:       "#EF4444",   // Erreurs, incorrect
          success:   "#10B981",   // Succès, correct
          border:    "#374151",   // Bordures subtiles
          muted:     "#9CA3AF",   // Texte secondaire
          text:      "#E5E7EB",   // Texte principal
          csdf:      "#1A3C5E",   // Couleur agence CSDF
        },
      },
      fontFamily: {
        mono: ["'Courier New'", "Courier", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      animation: {
        "blink": "blink 1s step-end infinite",
        "glow":  "glow 2s ease-in-out infinite alternate",
        "scan":  "scan 3s linear infinite",
        "fadeIn":"fadeIn 0.3s ease-in-out",
      },
      keyframes: {
        blink: {
          "0%, 100%": { opacity: "1" },
          "50%":       { opacity: "0" },
        },
        glow: {
          "0%":   { textShadow: "0 0 5px #00FF88" },
          "100%": { textShadow: "0 0 20px #00FF88, 0 0 40px #00FF88" },
        },
        scan: {
          "0%":   { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100vh)" },
        },
        fadeIn: {
          "0%":   { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      boxShadow: {
        "cyber-green": "0 0 20px rgba(0, 255, 136, 0.3)",
        "cyber-cyan":  "0 0 20px rgba(0, 212, 255, 0.3)",
        "cyber-red":   "0 0 20px rgba(239, 68, 68, 0.3)",
      },
    },
  },
  plugins: [],
};

export default config;
