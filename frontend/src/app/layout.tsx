import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Social Video RAG",
  description: "RAG chatbot for comparing social media video performance.",
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon.ico",
  },
};

/**
 * Root app layout. Page-level scroll is intentionally delegated to AppShell.
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
