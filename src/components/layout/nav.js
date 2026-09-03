import {
  LayoutDashboard,
  Database,
  BookOpen,
  Inbox,
  MessageSquare,
  LifeBuoy,
  Workflow,
  Plug,
  ScrollText,
  Settings,
} from "lucide-react";

/**
 * Navigation, grouped by what the person is actually doing:
 * looking at numbers, tending the knowledge, running the day, or
 * changing how the system behaves.
 */
export const NAV = [
  {
    group: "Overview",
    items: [{ to: "/admin", en: "Dashboard", ur: "ڈیش بورڈ", icon: LayoutDashboard, end: true }],
  },
  {
    group: "Knowledge",
    items: [
      { to: "/admin/content", en: "Content library", ur: "مواد", icon: Database },
      { to: "/admin/documents", en: "Source documents", ur: "دستاویزات", icon: BookOpen },
      { to: "/admin/flows", en: "Guided flows", ur: "رہنما مراحل", icon: Workflow },
      { to: "/admin/queue", en: "Review queue", ur: "جائزہ قطار", icon: Inbox, count: 14 },
    ],
  },
  {
    group: "Operations",
    items: [
      { to: "/admin/conversations", en: "Conversations", ur: "گفتگو", icon: MessageSquare },
      { to: "/admin/escalations", en: "Escalations", ur: "ایسکلیشن", icon: LifeBuoy, count: 4 },
    ],
  },
  {
    group: "System",
    items: [
      { to: "/admin/integrations", en: "Integrations", ur: "انضمام", icon: Plug },
      { to: "/admin/audit", en: "Audit log", ur: "آڈٹ لاگ", icon: ScrollText },
      { to: "/admin/guardrails", en: "Guardrails", ur: "حفاظتی اصول", icon: Settings },
    ],
  },
];
