import type { ChatMessage } from "@/lib/types";
import SourceChips from "./SourceChips";

export default function Message({
  message,
  isStreaming,
}: {
  message: ChatMessage;
  isStreaming?: boolean;
}) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] rounded-2xl bg-ink/5 px-4 py-2.5 text-[15px] leading-relaxed text-ink">
          {message.content}
        </div>
      </div>
    );
  }

  if (message.error) {
    return (
      <div className="border-l-2 border-error pl-4">
        <p className="font-serif text-sm uppercase tracking-wide text-error/80">
          Answer failed
        </p>
        <p className="mt-1 text-[15px] leading-relaxed text-ink/80">
          {message.error}
        </p>
      </div>
    );
  }

  return (
    <div className="border-l-2 border-pine pl-4">
      <p
        className={`whitespace-pre-wrap text-[15px] leading-relaxed text-ink ${
          isStreaming ? "streaming-cursor" : ""
        }`}
      >
        {message.content}
      </p>
      {message.sources && <SourceChips sources={message.sources} />}
    </div>
  );
}
