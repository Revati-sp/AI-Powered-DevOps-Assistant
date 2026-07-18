import type { Metadata } from "next";

import { UsagePageClient } from "@/components/usage/usage-page";

export const metadata: Metadata = {
  title: "Usage",
};

export default function UsagePage() {
  return <UsagePageClient />;
}
