import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f1419",
        mist: "#e8eef4",
        pine: "#1a6b4a",
        moss: "#2d9f6f",
        sand: "#f6f1ea",
        coral: "#c45c4a",
        dusk: "#3d4f5f",
      },
      fontFamily: {
        sans: ["var(--font-geist)", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "Georgia", "serif"],
      },
    },
  },
  plugins: [],
};

export default config;
