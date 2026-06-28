import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: "rgb(var(--color-cream) / <alpha-value>)",
        coral: "rgb(var(--color-coral) / <alpha-value>)",
        mint: "rgb(var(--color-mint) / <alpha-value>)",
        sunshine: "rgb(var(--color-sunshine) / <alpha-value>)",
        skysoft: "rgb(var(--color-skysoft) / <alpha-value>)",
        ink: "rgb(var(--color-ink) / <alpha-value>)",
        grape: "rgb(var(--color-grape) / <alpha-value>)",
        candy: "rgb(var(--color-candy) / <alpha-value>)",
      },
      boxShadow: {
        soft: "0 18px 50px rgba(23, 32, 51, 0.10)",
        glow: "0 22px 70px rgba(255, 122, 122, 0.22)",
        card: "0 18px 45px rgba(23, 32, 51, 0.08)",
      },
      borderRadius: {
        "3xl": "1.75rem",
      },
    },
  },
  plugins: [],
};

export default config;
