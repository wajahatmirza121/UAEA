import { Outlet, useLocation } from "react-router-dom";
import StudentHeader from "./StudentHeader";
import StudentFooter from "./StudentFooter";
import { useApp } from "@/context/AppContext";

/** Frame for every student page. The chat hides the footer so the composer
 *  stays pinned to the bottom of the viewport. */
export default function StudentShell() {
  const { theme } = useApp();
  const { pathname } = useLocation();
  const isChat = pathname.startsWith("/chat");

  return (
    <div className="uaea" data-theme={theme}>
      <div className="st">
        <StudentHeader />
        <main className="st-main">
          <Outlet />
        </main>
        {!isChat && <StudentFooter />}
      </div>
    </div>
  );
}
