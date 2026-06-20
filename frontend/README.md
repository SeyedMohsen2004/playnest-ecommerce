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

Create `.env.local` from `.env.example`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Some pages still use mock data where backend integration is planned, while the
main ecommerce flow is being connected incrementally to the Django API.

## Legal and Business Pages

The frontend includes draft Persian pages for about, contact, terms, privacy,
returns, shipping, and shopping guide content. These are placeholder drafts for
development and portfolio review. Before production, the business owner must
replace sample contact details, Enamad placeholder, legal copy, shipping terms,
return rules, and privacy details with approved real business information.

## Quality

```bash
npm run lint
npm run build
```
