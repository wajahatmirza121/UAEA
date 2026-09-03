import { useState } from "react";
import { Upload } from "lucide-react";
import DocumentList from "./DocumentList";
import RetrievalTester from "./RetrievalTester";
import UploadProgress, { UPLOAD_STAGES } from "./UploadProgress";
import Button from "@/components/ui/Button";
import { can } from "@/lib/rbac";
import { useApp } from "@/context/AppContext";
import { useToast } from "@/context/ToastContext";

export default function Documents() {
  const { store, role } = useApp();
  const toast = useToast();
  const [uploading, setUploading] = useState(false);
  const [stage, setStage] = useState(0);

  const mayWrite = can(role, "documents.write");

  // ↯ API SEAM — POST /v1/admin/content/documents, then poll ingestion status
  const runUpload = () => {
    setUploading(true);
    setStage(0);
    let s = 0;
    const tick = () => {
      s += 1;
      setStage(s);
      if (s < UPLOAD_STAGES.length - 1) {
        setTimeout(tick, 620);
      } else {
        setTimeout(() => {
          setUploading(false);
          toast("Document indexed", "Older versions of this circular were superseded, not duplicated.");
        }, 700);
      }
    };
    setTimeout(tick, 620);
  };

  return (
    <div className="ua-page">
      <div className="ua-head">
        <div>
          <h1 className="ua-h1">Source documents</h1>
          <p className="ua-sub">
            Prospectuses, circulars and manuals the assistant quotes from. New versions supersede old
            ones so students never get two answers to the same question.
          </p>
        </div>
        {mayWrite && (
          <Button variant="primary" icon={Upload} onClick={runUpload} loading={uploading}>
            {uploading ? UPLOAD_STAGES[stage] : "Upload document"}
          </Button>
        )}
      </div>

      {uploading && <UploadProgress stage={stage} />}

      <div className="ua-cols two">
        <DocumentList documents={store.documents} />
        <RetrievalTester />
      </div>
    </div>
  );
}
