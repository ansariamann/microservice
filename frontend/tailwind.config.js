/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#0a0a0f",
        surface: "#12121a",
        primary: "#6366f1", // Indigo 500
        secondary: "#ec4899", // Pink 500
        accent: "#8b5cf6", // Violet 500
        "primary-glow": "rgba(99, 102, 241, 0.4)",
        "secondary-glow": "rgba(236, 72, 153, 0.4)",
      },
      fontFamily: {
        sans: ['"Outfit"', "sans-serif"],
      },
      animation: {
        float: "float 6s ease-in-out infinite",
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        shimmer: "shimmer 2.5s linear infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-20px)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};
