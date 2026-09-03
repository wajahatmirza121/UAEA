import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppProvider } from "@/context/AppContext";
import { ToastProvider } from "@/context/ToastContext";

import StudentShell from "@/components/student/StudentShell";
import Landing from "@/pages/student/Landing";
import Chat from "@/pages/student/Chat";
import Services from "@/pages/student/Services";
import ServiceDetail from "@/pages/student/Services/ServiceDetail";
import Directory from "@/pages/student/Directory";

import AppShell from "@/components/layout/AppShell";
import Dashboard from "@/pages/Dashboard";
import ContentLibrary from "@/pages/ContentLibrary";
import Documents from "@/pages/Documents";
import GuidedFlows from "@/pages/GuidedFlows";
import ReviewQueue from "@/pages/ReviewQueue";
import Conversations from "@/pages/Conversations";
import Escalations from "@/pages/Escalations";
import Integrations from "@/pages/Integrations";
import AuditLog from "@/pages/AuditLog";
import GuardrailsPage from "@/pages/Guardrails";

/**
 * Two faces on one data layer.
 *
 *   /        the student site — the product itself
 *   /admin   the staff console — the back office that keeps it honest
 *
 * The student side sits at the root because that is who arrives at this URL.
 * Both read the same catalogue, which is the point: an editor changing a fee
 * in the console changes what the assistant tells students on the next turn.
 */
export default function App() {
  return (
    <AppProvider>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            {/* — student — */}
            <Route element={<StudentShell />}>
              <Route path="/" element={<Landing />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/services" element={<Services />} />
              <Route path="/services/:id" element={<ServiceDetail />} />
              <Route path="/directory" element={<Directory />} />
            </Route>

            {/* — staff console — */}
            <Route path="/admin" element={<AppShell />}>
              <Route index element={<Dashboard />} />
              <Route path="content" element={<ContentLibrary />} />
              <Route path="documents" element={<Documents />} />
              <Route path="flows" element={<GuidedFlows />} />
              <Route path="queue" element={<ReviewQueue />} />
              <Route path="conversations" element={<Conversations />} />
              <Route path="escalations" element={<Escalations />} />
              <Route path="integrations" element={<Integrations />} />
              <Route path="audit" element={<AuditLog />} />
              <Route path="guardrails" element={<GuardrailsPage />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </AppProvider>
  );
}
