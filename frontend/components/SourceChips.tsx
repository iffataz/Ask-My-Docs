"use client";

import { useState } from "react";
import type { Source } from "@/lib/types";

export default function SourceChips({ sources }: { sources: Source[] }) {
  const [expanded, setExpanded] = useState<number | null>(null);

  if (sources.length === 0) return null;

  return (
    <div className="mt-3 flex flex-col gap-1.5">
      <div className="flex flex-wrap gap-2">
        {sources.map((source, i) => (
          <button
            key={`${source.filename}-${source.chunk_index}-${i}`}
            onClick={() => setExpanded(expanded === i ? null : i)}
            className="rounded-full border border-hairline px-2.5 py-1 font-mono text-xs text-ink/70 transition-colors hover:border-brown hover:text-brown"
          >
            {source.filename} <span className="text-ink/40">·</span> chunk{" "}
            {source.chunk_index}
          </button>
        ))}
      </div>
      {expanded !== null && (
        <div className="border-l-2 border-brown bg-brown/5 px-3 py-2">
          <p className="font-mono text-[11px] uppercase tracking-wide text-brown">
            {sources[expanded].filename} — chunk {sources[expanded].chunk_index}
          </p>
          <p className="mt-1.5 max-h-48 overflow-y-auto whitespace-pre-wrap text-xs leading-relaxed text-ink/80">
            {sources[expanded].text}
          </p>
        </div>
      )}
    </div>
  );
}
