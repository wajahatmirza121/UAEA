import { FileText, Banknote, Calendar, Building2 } from "lucide-react";

/** The four tables that make up the deterministic backbone (§4.4, §6). */
export const CONTENT_TABS = [
  { id: "services", label: "Services", icon: FileText },
  { id: "fees", label: "Fee tariff", icon: Banknote },
  { id: "deadlines", label: "Deadlines", icon: Calendar },
  { id: "departments", label: "Departments", icon: Building2 },
];
