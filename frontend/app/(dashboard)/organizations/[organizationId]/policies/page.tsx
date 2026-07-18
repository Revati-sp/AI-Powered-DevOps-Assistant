import type { Metadata } from "next";

import { PolicyPacksPageClient } from "@/components/policies/policy-packs-page";

export const metadata: Metadata = {
  title: "Policies",
};

type Props = {
  params: Promise<{ organizationId: string }>;
};

export default async function PoliciesPage({ params }: Props) {
  const { organizationId } = await params;
  return <PolicyPacksPageClient organizationId={organizationId} />;
}
