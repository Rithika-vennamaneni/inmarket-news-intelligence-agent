/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#05051A",
        slateNight: "#0D0D2B",
        bubble: "#0D0D2B",
        accent: "#0047FF",
        muted: "#8A8AA0",
      },
      boxShadow: {
        panel: "0 24px 80px rgba(5, 5, 26, 0.42)",
      },
    },
  },
  plugins: [],
};
