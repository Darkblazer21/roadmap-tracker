/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Pomodoro states
        pomo: { work: "#dc2626", short: "#16a34a", long: "#2563eb" },
      },
    },
  },
  plugins: [],
};