import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { ThemeProvider } from "next-themes";
import "./prismui.css";
import "./styles.css";
import "./apple-design.css";
import "./design-options.css";
import "./theme-consistency.css";
import "./workflow-layout.css";
import "./designPreview";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem disableTransitionOnChange>
      <App />
    </ThemeProvider>
  </React.StrictMode>,
);
