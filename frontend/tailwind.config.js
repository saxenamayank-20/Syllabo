// Neutrals come from CSS variables (see index.css) so the light and dark themes share one set of classes.
const themed = (name) => `rgb(var(--${name}) / <alpha-value>)`
const SLATE_STEPS = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900]

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'] },
      colors: {
        primary: {
          50: '#eff6ff', 100: '#dbeafe', 200: '#bfdbfe', 300: '#93c5fd', 400: '#60a5fa', 500: '#3b82f6',
          600: '#2563eb', 700: '#1d4ed8',
        },
        slate: Object.fromEntries(SLATE_STEPS.map((step) => [step, themed(`slate-${step}`)])),
        canvas: themed('canvas'),
        surface: themed('surface'),
      },
      boxShadow: {
        card: 'var(--shadow-card)',
      },
    },
  },
  plugins: [],
}
