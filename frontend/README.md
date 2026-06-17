# PlayNest Frontend

Initial Persian-first, RTL Next.js frontend for PlayNest Ecommerce.

## Stack

- Next.js App Router
- TypeScript
- Tailwind CSS
- shadcn/ui-inspired primitives
- lucide-react icons
- Persian-first RTL interface

## Setup

```bash
npm install
cp .env.example .env.local
npm run dev
```

The development server runs at `http://localhost:3000`.

## Environment

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

The current UI uses static mock data and does not call backend APIs yet.

## Quality

```bash
npm run lint
npm run build
```
