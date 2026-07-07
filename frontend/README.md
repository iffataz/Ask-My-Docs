# Frontend

Next.js chat UI for Ask My Docs — streaming answers with expandable source citations, and a document sidebar (drag-drop upload, list, delete).

## Setup

```bash
cd frontend
npm install
cp ../.env.example ../.env   # sets NEXT_PUBLIC_API_URL (default http://localhost:8000)
```

See the [backend README](../backend/README.md) for starting the API — the frontend calls it directly (no proxy layer), so it must be running on the URL configured above.

## Run

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Lint / typecheck / build

```bash
npm run lint
npm run typecheck
npm run build
```
