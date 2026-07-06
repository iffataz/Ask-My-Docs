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
        <div className="border-l-2 border-brown bg-brown/5 px-3 py-2 font-mono text-xs text-ink/70">
          {sources[expanded].filename} — chunk {sources[expanded].chunk_index}{" "}
          consulted to ground this answer.
        </div>
      )}
    </div>
  );
}
