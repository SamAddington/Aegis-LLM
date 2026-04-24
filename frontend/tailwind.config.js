/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        aegis: {
          bg: "#0b1120",
          panel: "#111a2e",
          border: "#1e293b",
          accent: "#22d3ee",
          danger: "#f43f5e",
          safe: "#22c55e",
          warn: "#f59e0b",
          muted: "#64748b",
        },
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};
