import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { PostHogProvider } from "@posthog/react";
import App from "./App";
import "./styles.css";

const posthogKey = import.meta.env.VITE_POSTHOG_PROJECT_TOKEN || "phc_pJtabWfJceqtT6otFV7CyG8Zt2FXYWhrx3CeegW7AJk7";
const posthogHost = import.meta.env.VITE_POSTHOG_HOST || "https://us.i.posthog.com";

const posthogOptions = {
  api_host: posthogHost,
  defaults: "2026-05-30" as const,
  autocapture: true,
  session_recording: {
    recordCrossOriginIframes: true,
  },
};

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {posthogKey ? (
      <PostHogProvider apiKey={posthogKey} options={posthogOptions}>
        <App />
      </PostHogProvider>
    ) : (
      <App />
    )}
  </StrictMode>,
);

