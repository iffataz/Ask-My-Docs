"use client";

import { useRef, useState } from "react";
import type { DocumentInfo } from "@/lib/types";
import { ApiError, deleteDocument, listDocuments, uploadDocument } from "@/lib/api";

export default function DocumentSidebar({
  documents,
  setDocuments,
}: {
  documents: DocumentInfo[];
  setDocuments: React.Dispatch<React.SetStateAction<DocumentInfo[]>>;
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    setIsUploading(true);
    setError(null);
    try {
      const uploaded = await uploadDocument(file);
      setDocuments((prev) => [
        ...prev,
        {
          document_id: uploaded.document_id,
          filename: uploaded.filename,
          chunk_count: uploaded.chunk_count,
        },
      ]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleDelete(documentId: string) {
    const previous = documents;
    setDocuments((prev) => prev.filter((d) => d.document_id !== documentId));
    try {
      await deleteDocument(documentId);
    } catch {
      setDocuments(previous);
      try {
        setDocuments(await listDocuments());
      } catch {
        setDocuments(previous);
      }
    }
  }

  return (
    <aside className="flex h-full w-72 flex-col border-r border-hairline bg-paper">
      <div className="px-5 pt-6 pb-4">
        <h1 className="font-serif text-lg text-ink">Ask My Docs</h1>
        <p className="mt-1 text-xs text-ink/50">
          Upload documents, then ask questions grounded in them.
        </p>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          const file = e.dataTransfer.files[0];
          if (file) void handleFile(file);
        }}
        className={`mx-5 flex flex-col items-center justify-center rounded-lg border border-dashed px-3 py-6 text-center transition-colors ${
          isDragging ? "border-pine bg-pine/5" : "border-hairline"
        }`}
      >
        <p className="text-xs text-ink/60">
          Drag a .pdf, .md, or .txt file here
        </p>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="mt-2 text-xs font-medium text-pine underline underline-offset-2 hover:text-pine-dim disabled:opacity-50"
        >
          {isUploading ? "Uploading…" : "or choose a file"}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.md,.txt"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleFile(file);
            e.target.value = "";
          }}
        />
      </div>

      {error && (
        <p className="mx-5 mt-2 text-xs text-error">{error}</p>
      )}

      <div className="mt-5 flex-1 overflow-y-auto px-5">
        <p className="font-mono text-[11px] uppercase tracking-wide text-ink/40">
          Documents
        </p>
        {documents.length === 0 ? (
          <p className="mt-3 text-sm text-ink/40">No documents yet.</p>
        ) : (
          <ul className="mt-2 flex flex-col gap-1">
            {documents.map((doc) => (
              <li
                key={doc.document_id}
                className="group flex items-center justify-between gap-2 rounded py-1.5"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm text-ink">{doc.filename}</p>
                  <p className="font-mono text-[11px] text-ink/40">
                    {doc.chunk_count} chunks
                  </p>
                </div>
                <button
                  onClick={() => handleDelete(doc.document_id)}
                  aria-label={`Delete ${doc.filename}`}
                  className="text-ink/30 opacity-0 transition-opacity hover:text-error group-hover:opacity-100"
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}
