"use client";

import { useEffect, useState } from "react";
import type { ChatMessage, DocumentInfo } from "@/lib/types";
import { listDocuments } from "@/lib/api";
import DocumentSidebar from "@/components/DocumentSidebar";
import ChatPanel from "@/components/ChatPanel";

export default function Home() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId] = useState(() => crypto.randomUUID());

  useEffect(() => {
    listDocuments()
      .then(setDocuments)
      .catch(() => setDocuments([]));
  }, []);

  return (
    <div className="flex h-screen">
      <DocumentSidebar documents={documents} setDocuments={setDocuments} />
      <main className="flex-1">
        <ChatPanel
          messages={messages}
          setMessages={setMessages}
          sessionId={sessionId}
        />
      </main>
    </div>
  );
}
