This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

---

## System Architecture & Documentation

For details on the overall system design and database implementation, refer to:
* **[System Design Specification](../docs/system_design.md)**: Visual diagrams of backend agent flows, approval states, and Firestore JSON schemas.
* **[Database README](../app/db/README.md)**: Guide on the local JSON file database and live Google Cloud Firestore configuration.

---

## Agent Tools Integration

The Next.js web application interfaces with the custom backend tools configured on the Vertex AI Reasoning Engine agent. The database status changes triggered in the UI align with these tools:

* **Employee Verification**: Binds to `lookup_employee` to pull profile details, cost centers, and department information.
* **Request Validation**: Calls `check_existing_requests` to determine cooldown blocks and detect policy bypasses (e.g., defective or damaged laptops).
* **Entitlement Resolution**: Syncs with `check_policy` evaluations which decide standard vs. premium tiers and approval paths (Auto-approve vs. Manager).
* **Ticket Management**: Invokes `create_ticket`, `approve_request`, and `mark_received` state updates, building a persistent audit trail.

