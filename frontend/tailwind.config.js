/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        forest: "#163B2C", deep: "#10291F", leaf: "#6FAF76", soft: "#EAF3EA", warm: "#F8FAF7",
        charcoal: "#202A25", muted: "#78847D", amber: "#D9A441", danger: "#C84C4C",
      },
      fontFamily: { sans: ["Manrope", "Inter", "system-ui", "sans-serif"] },
    },
  },
  plugins: [],
};
