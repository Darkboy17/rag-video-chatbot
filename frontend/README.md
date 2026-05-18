# Social Video RAG Frontend

Next.js workspace UI for the Social Video RAG Chatbot. The frontend accepts two
social video URLs, streams backend analysis progress, renders the comparison
cards, and provides a streamed RAG chat panel with source citations.

## Setup

```powershell
npm install
copy .env.example .env.local
npm run dev
```

The app runs at `http://localhost:3000` and expects the backend at
`NEXT_PUBLIC_API_BASE_URL`, which defaults to `http://localhost:8000` in
`.env.example`.

## Scripts

- `npm run dev` starts the local development server.
- `npm run lint` runs ESLint.
- `npm run build` creates a production build.

## Main Areas

- `src/app` contains the workspace route and global styling.
- `src/components/video` contains URL input, progress, video cards, and summary UI.
- `src/components/chat` contains the streamed chat interface and source list.
- `src/hooks` owns analysis and chat streaming state.
- `src/lib` contains API and SSE helpers.

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
