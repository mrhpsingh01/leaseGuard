import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        uga: {
          red: "#BA0C2F",
          black: "#000000",
          arch: "#6E1B24",
          cream: "#FAF9F6",
        },
        guard: {
          dark: "#0F172A",
          slate: "#1E293B",
          border: "#334155",
          accent: "#2563EB",
          crimson: "#DC2626",
          amber: "#D97706",
          emerald: "#059669",
        }
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      }
    },
  },
  plugins: [],
};
export default config;
