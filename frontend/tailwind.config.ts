import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: "#fff8ed",
        coral: "#ff7a7a",
        mint: "#6ee7b7",
        sunshine: "#ffd166",
        skysoft: "#dff5ff",
        ink: "#172033",
      },
      boxShadow: {
        soft: "0 18px 50px rgba(23, 32, 51, 0.10)",
      },
      borderRadius: {
        "3xl": "1.75rem",
      },
    },
  },
  plugins: [],
};

export default config;
