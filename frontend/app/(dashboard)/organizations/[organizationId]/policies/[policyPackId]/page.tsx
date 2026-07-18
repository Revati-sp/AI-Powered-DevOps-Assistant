import type { Metadata } from "next";

import { PolicyPackDetail } from "@/components/policies/policy-pack-detail";

export const metadata: Metadata = {
  title: "Policy pack",
};

type Props = {
  params: Promise<{ organizationId: string; policyPackId: string }>;
};

export default async function PolicyPackDetailPage({ params }: Props) {
  const { organizationId, policyPackId } = await params;
  return <PolicyPackDetail organizationId={organizationId} policyPackId={policyPackId} />;
}
