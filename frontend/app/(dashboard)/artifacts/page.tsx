import type { Metadata } from "next";

import { ArtifactsPageClient } from "@/components/artifacts/artifacts-page";

export const metadata: Metadata = {
  title: "Artifacts",
};

export default function ArtifactsPage() {
  return <ArtifactsPageClient />;
}
