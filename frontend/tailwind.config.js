/** @type {import('tailwindcss').Config} */

// Colors are CSS variables (see globals.css) so light/dark themes swap in one place
const token = (name) => `rgb(var(--${name}) / <alpha-value>)`;

module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-inter)', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      colors: {
        canvas: token('canvas'),
        surface: token('surface'),
        subtle: token('subtle'),
        line: token('line'),
        ink: token('ink'),
        muted: token('muted'),
        accent: token('accent'),
        'on-accent': token('on-accent'),
        risk: {
          stable: token('stable'),
          elevated: token('elevated'),
          critical: token('critical'),
        },
      },
    },
  },
  plugins: [],
}
