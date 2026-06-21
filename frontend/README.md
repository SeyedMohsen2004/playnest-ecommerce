# IpakToys Frontend

Persian-first, RTL Next.js frontend for the IpakToys ecommerce storefront.
The UI is focused on board games, intellectual games, puzzles, building games,
and educational entertainment products for children, teenagers, and families.

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

Products, authentication, cart, checkout, and payment pages are connected to the
Django API. Mock data remains as a fallback for development when the backend is
unavailable.

## Legal and Business Pages

The frontend includes draft Persian pages for about, contact, terms, privacy,
returns, shipping, and shopping guide content. The current customer-facing brand
is IpakToys, and contact placeholders have been updated with the provided
business information.

Before production, the business owner should review and approve legal copy,
shipping terms, return rules, privacy details, and Enamad placement.

## Quality

```bash
npm run lint
npm run build
```
