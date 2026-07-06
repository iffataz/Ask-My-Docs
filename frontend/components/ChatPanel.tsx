"use client";

import { useEffect, useRef, useState } from "react";
import type { ChatMessage } from "@/lib/types";
import { streamChat } from "@/lib/sse";
import Message from "./Message";

export default function ChatPanel({
  messages,
  setMessages,
  sessionId,
}: {
  messages: ChatMessage[];
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  sessionId: string;
}) {
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [streamingId, setStreamingId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || isThinking || streamingId) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
    };
    const assistantId = crypto.randomUUID();
    const assistantMessage: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setInput("");
    setIsThinking(true);

    let firstToken = true;

    await streamChat(question, sessionId, {
      onToken: (text) => {
        if (firstToken) {
          firstToken = false;
          setIsThinking(false);
          setStreamingId(assistantId);
        }
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: m.content + text } : m
          )
        );
      },
      onDone: (sources) => {
        setIsThinking(false);
        setStreamingId(null);
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, sources } : m))
        );
      },
      onError: (detail) => {
        setIsThinking(false);
        setStreamingId(null);
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, error: detail } : m))
        );
      },
    });
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="mx-auto flex max-w-2xl flex-col gap-6">
          {messages.length === 0 && (
            <div className="mt-16 text-center">
              <p className="font-serif text-xl text-ink/60">
                Ask a question about your documents
              </p>
              <p className="mt-2 text-sm text-ink/40">
                Answers cite the exact chunks they&rsquo;re grounded in.
              </p>
            </div>
          )}
          {messages.map((message) => (
            <Message
              key={message.id}
              message={message}
              isStreaming={message.id === streamingId}
            />
          ))}
          {isThinking && (
            <div className="border-l-2 border-pine/30 pl-4">
              <p className="text-sm text-ink/40">Thinking…</p>
            </div>
          )}
          <div ref={scrollRef} />
        </div>
      </div>
      <form
        onSubmit={handleSubmit}
        className="border-t border-hairline px-8 py-4"
      >
        <div className="mx-auto flex max-w-2xl gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question…"
            disabled={isThinking || !!streamingId}
            className="flex-1 rounded-full border border-hairline bg-white px-4 py-2.5 text-[15px] text-ink placeholder:text-ink/40 focus:border-pine focus:outline-none disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isThinking || !!streamingId || !input.trim()}
            className="rounded-full bg-pine px-5 py-2.5 text-sm font-medium text-paper transition-colors hover:bg-pine-dim disabled:opacity-40"
          >
            Ask
          </button>
        </div>
      </form>
    </div>
  );
}
