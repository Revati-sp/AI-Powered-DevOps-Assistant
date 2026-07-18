import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import { APP_NAME } from "@/lib/constants/app";
import { AppProviders } from "@/providers/app-providers";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: APP_NAME,
    template: `%s · ${APP_NAME}`,
  },
  description:
    "AI-powered DevOps assistant for log analysis, infrastructure generation, reviews, and chat.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="bg-background text-foreground flex min-h-full flex-col font-sans">
        <a
          href="#main-content"
          className="bg-primary text-primary-foreground focus:ring-ring sr-only focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:z-50 focus:rounded-md focus:px-3 focus:py-2 focus:ring-2"
        >
          Skip to content
        </a>
        <AppProviders>
          <div className="flex min-h-full flex-1 flex-col">{children}</div>
        </AppProviders>
      </body>
    </html>
  );
}
