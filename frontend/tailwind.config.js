/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#09090B",
        card: "#1C1917",
        surface: "#141210",
        accent: "#F97316",
        "accent-dark": "#C2410C",
        border: "#27272A",
        "border-light": "#3F3F46",
        muted: "#A1A1AA",
        faint: "#52525B",
      },
      boxShadow: {
        glow: "0 0 24px rgba(249,115,22,0.25)",
        "glow-lg": "0 0 48px rgba(249,115,22,0.3)",
      },
      animation: {
        "spin-slow": "spin 3s linear infinite",
        blink: "blink 1s step-end infinite",
      },
      keyframes: {
        blink: { "0%,100%": { opacity: "1" }, "50%": { opacity: "0" } },
      },
    },
  },
  plugins: [],
};
