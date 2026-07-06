export interface DocumentInfo {
  document_id: string;
  filename: string;
  chunk_count: number;
}

export interface Source {
  filename: string;
  chunk_index: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  error?: string;
}
