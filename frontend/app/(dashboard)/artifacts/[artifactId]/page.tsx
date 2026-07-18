import type { Metadata } from "next";

import { ArtifactDetail } from "@/components/artifacts/artifact-detail";

export const metadata: Metadata = {
  title: "Artifact",
};

type Props = {
  params: Promise<{ artifactId: string }>;
};

export default async function ArtifactDetailPage({ params }: Props) {
  const { artifactId } = await params;
  return <ArtifactDetail artifactId={artifactId} />;
}
