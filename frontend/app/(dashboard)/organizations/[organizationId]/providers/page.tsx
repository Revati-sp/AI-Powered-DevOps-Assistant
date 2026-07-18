import type { Metadata } from "next";

import { ProvidersPageClient } from "@/components/providers/providers-page";

export const metadata: Metadata = {
  title: "Providers",
};

type Props = {
  params: Promise<{ organizationId: string }>;
};

export default async function ProvidersPage({ params }: Props) {
  const { organizationId } = await params;
  return <ProvidersPageClient organizationId={organizationId} />;
}
