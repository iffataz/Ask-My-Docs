import type { DocumentInfo } from "./types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string };
    return body.detail ?? response.statusText;
  } catch {
    return response.statusText;
  }
}

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  chunk_count: number;
}

export async function uploadDocument(
  file: File
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/documents`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response));
  }

  return (await response.json()) as DocumentUploadResponse;
}

export async function listDocuments(): Promise<DocumentInfo[]> {
  const response = await fetch(`${API_URL}/documents`);

  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response));
  }

  return (await response.json()) as DocumentInfo[];
}

export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetch(`${API_URL}/documents/${documentId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response));
  }
}
