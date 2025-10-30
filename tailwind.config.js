/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",

  content: [
    "./templates/**/*.html",
    "./**/templates/**/*.html",
    "./static/src/**/*.{js,ts}",
    "./node_modules/preline/dist/*.js",
  ],

  theme: {
    extend: {
      /* ==============================
         🅰️ TYPOGRAPHIE ESFÉ MODERNISÉE
      =============================== */
      fontFamily: {
        display: ["'Plus Jakarta Sans'", "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ["'DM Sans'", "ui-sans-serif", "system-ui", "sans-serif"],
      },

      /* ==============================
         🎨 PALETTE OFFICIELLE ESFÉ
      =============================== */
      colors: {
        primary: {
          50: "#f1f5fb",
          100: "#e4ebf7",
          200: "#c3d1eb",
          300: "#9cb3dc",
          400: "#5c83c3",
          500: "#1e4da1",
          600: "#173e83",
          700: "#12346e",
          800: "#0f2c5e",
          900: "#0c2d5a",
        },
        accent: { DEFAULT: "#22D3EE" },
        brand: { light: "#3FA9F5", cyan: "#22D3EE" },
        success: { DEFAULT: "#16A34A" },
        warning: { DEFAULT: "#F59E0B" },
        danger: { DEFAULT: "#DC2626" },
        info: { DEFAULT: "#0284C7" },
        slate: { 950: "#0B1221" },
      },

      /* ==============================
         🧩 STYLES VISUELS
      =============================== */
      boxShadow: {
        soft: "0 8px 24px rgba(0,0,0,.06)",
        focus: "0 0 0 3px rgba(30,77,161,.35)",
        card: "0 2px 8px rgba(15,23,42,0.08)",
      },
      borderRadius: {
        "2xl": "1.25rem",
        "3xl": "1.75rem",
      },
      maxWidth: {
        container: "72rem",
      },
      transitionTimingFunction: {
        "in-out-soft": "cubic-bezier(0.22, 1, 0.36, 1)",
      },
    },
  },

  plugins: [require("preline/plugin")],
};
