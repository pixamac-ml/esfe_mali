/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./**/templates/**/*.html",     // ← capte les templates dans chaque app
    "./static/src/**/*.{js,ts}"     // ← scripts qui portent des classes
    // "./**/*.py",                  // optionnel : tu peux l’enlever pour accélérer le build
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["Archivo", "Inter", "ui-sans-serif", "system-ui"],
        sans: ["Inter", "Source Sans 3", "ui-sans-serif", "system-ui"],
      },
      colors: {
        primary: {
          50:"#F2F6FB",100:"#E6EEF7",200:"#C6D5EA",300:"#9EB7DB",
          400:"#5B84C3",500:"#1E4DA1",600:"#173E83",700:"#12346E",
          800:"#0F2C5E",900:"#0C2D5A"
        },
        brand: { light:"#3FA9F5", cyan:"#22D3EE" },
        accent: { DEFAULT:"#22D3EE" },
        success:{ DEFAULT:"#16A34A" },
        warning:{ DEFAULT:"#F59E0B" },
        danger: { DEFAULT:"#DC2626" },
        info:   { DEFAULT:"#0284C7" },
      },
      boxShadow: {
        soft: "0 8px 24px rgba(0,0,0,.06)",
        focus: "0 0 0 3px rgba(30,77,161,.35)",
      },
      borderRadius: { "2xl": "1.25rem" },
      maxWidth: { container: "72rem" },
    },
  },
  plugins: [],
};
