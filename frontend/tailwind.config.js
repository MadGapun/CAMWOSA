export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        camwosa: {
          bg: "#1a1a1a",
          surface: "#252525",
          accent: "#ff6b00",
          warn: "#ffc107",
          danger: "#dc3545",
          ok: "#28a745",
          text: "#e8e8e8",
          muted: "#888888",
        },
      },
    },
  },
  plugins: [],
};
