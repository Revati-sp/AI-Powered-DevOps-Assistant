import type { Metadata } from "next";

import { LogAnalyzer } from "@/components/logs/log-analyzer";

export const metadata: Metadata = {
  title: "Log Analyzer",
};

export default function LogsPage() {
  return <LogAnalyzer />;
}
