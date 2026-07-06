import { API_URL } from "./api";
import type { Source } from "./types";

export interface StreamChatHandlers {
  onToken: (text: string) => void;
  onDone: (sources: Source[]) => void;
  onError: (detail: string) => void;
}

function parseFrame(frame: string): { event: string; data: string } | null {
  let event = "message";
  let data = "";
  for (const line of frame.split("\n")) {
    if (line.startsWith("event:")) {
      event = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      data = line.slice("data:".length).trim();
    }
  }
  return data ? { event, data } : null;
}

export async function streamChat(
  question: string,
  sessionId: string,
  handlers: StreamChatHandlers
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, session_id: sessionId }),
    });
  } catch {
    handlers.onError("Could not reach the server");
    return;
  }

  if (!response.ok || !response.body) {
    handlers.onError("Could not reach the server");
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let done = false;

  try {
    while (true) {
      const { value, done: streamDone } = await reader.read();
      if (streamDone) break;

      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split("\n\n");
      buffer = frames.pop() ?? "";

      for (const rawFrame of frames) {
        const parsed = parseFrame(rawFrame);
        if (!parsed) continue;

        if (parsed.event === "token") {
          const { text } = JSON.parse(parsed.data) as { text: string };
          handlers.onToken(text);
        } else if (parsed.event === "done") {
          const { sources } = JSON.parse(parsed.data) as { sources: Source[] };
          handlers.onDone(sources);
          done = true;
        } else if (parsed.event === "error") {
          const { detail } = JSON.parse(parsed.data) as { detail: string };
          handlers.onError(detail);
          done = true;
        }
      }
    }
  } catch {
    if (!done) handlers.onError("Connection to the server was lost");
    return;
  }

  if (!done) handlers.onError("Connection to the server was lost");
}
