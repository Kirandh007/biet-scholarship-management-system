export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#08172f",
        primary: "#132f8a",
        indigoDeep: "#071a55",
        emeraldPro: "#0f9f6e",
        goldPro: "#f5b84b",
        cyanPro: "#19d3ff"
      },
      boxShadow: {
        premium: "0 24px 80px rgba(8, 23, 47, 0.18)",
        glow: "0 0 45px rgba(25, 211, 255, 0.25)"
      },
      backgroundImage: {
        aurora: "radial-gradient(circle at top left, rgba(25,211,255,.22), transparent 28%), radial-gradient(circle at top right, rgba(245,184,75,.20), transparent 26%), linear-gradient(135deg, #eef6ff 0%, #f8fbff 45%, #eefdf7 100%)"
      }
    }
  },
  plugins: []
};
