import { useEffect } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import EmergencyRequest from "./pages/EmergencyRequest";
import OfflineBanner from "./components/OfflineBanner";

function App() {

  // Register Service Worker
  useEffect(() => {
    if ("serviceWorker" in navigator) {
      window.addEventListener("load", () => {
        navigator.serviceWorker
          .register("/sw.js")
          .then((reg) => {
            console.log("✅ Service Worker registered:", reg.scope);

            // Listen for SW updates
            reg.addEventListener("updatefound", () => {
              const newWorker = reg.installing;
              newWorker?.addEventListener("statechange", () => {
                if (
                  newWorker.state === "installed" &&
                  navigator.serviceWorker.controller
                ) {
                  console.log("🔄 New Service Worker available — refresh to update");
                }
              });
            });
          })
          .catch((err) => console.error("❌ Service Worker failed:", err));
      });
    }
  }, []);

  return (
    <Router>
      {/* OfflineBanner sits outside Routes — visible on every page */}
      <OfflineBanner />

      <Routes>
        <Route path="/"                  element={<Home />} />
        <Route path="/emergency-request" element={<EmergencyRequest />} />

        {/* ── Future routes (add as you build them) ──────────
        <Route path="/dashboard"   element={<Dashboard />} />
        <Route path="/donations"   element={<Donations />} />
        ─────────────────────────────────────────────────── */}
      </Routes>
    </Router>
  );
}

export default App;
