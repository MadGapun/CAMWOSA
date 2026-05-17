import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, HashRouter } from "react-router-dom";
import App from "./App";
import "./i18n";
import "./styles/index.css";

const root = document.getElementById("root");
if (!root) throw new Error("Kein #root-Element gefunden");

// BrowserRouter funktioniert unter file:// nicht (HTML5-History-API mit
// echten Pfaden braucht http(s)). In Electron-Production landen wir auf
// file:///.../index.html — Navigate to="/quickstart" wuerde dann auf
// file:///quickstart zeigen und 404 geben. Deshalb HashRouter im Bundle.
// Im Dev (http://localhost:5173) bleibt BrowserRouter sauber.
const Router = window.location.protocol === "file:" ? HashRouter : BrowserRouter;

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <Router>
      <App />
    </Router>
  </React.StrictMode>,
);
