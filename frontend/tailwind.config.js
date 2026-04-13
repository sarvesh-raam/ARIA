/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-inter)'],
        display: ['var(--font-outfit)'],
      },
      colors: {
        background: "#020617",
        foreground: "#f8fafc",
        card: {
          DEFAULT: "#0f172a",
          hover: "#1e293b",
        },
        brand: {
          DEFAULT: "#06b6d4",
          light: "#22d3ee",
          dark: "#0891b2",
        },
        risk: {
          stable: "#10b981",
          elevated: "#f59e0b",
          critical: "#ef4444",
        }
      },
      boxShadow: {
        'glow-cyan': '0 0 15px rgba(6, 182, 212, 0.3)',
        'glow-red': '0 0 15px rgba(239, 68, 68, 0.3)',
      },
      backgroundImage: {
        'mesh-glow': 'radial-gradient(at 0% 0%, rgba(6, 182, 212, 0.15) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(139, 92, 246, 0.1) 0px, transparent 50%)',
      },
    },
  },
  plugins: [],
}
