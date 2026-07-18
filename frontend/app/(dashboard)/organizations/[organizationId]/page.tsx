import type { Metadata } from "next";

import { OrganizationDetail } from "@/components/organizations/organization-detail";

export const metadata: Metadata = {
  title: "Organization",
};

type Props = {
  params: Promise<{ organizationId: string }>;
};

export default async function OrganizationDetailPage({ params }: Props) {
  const { organizationId } = await params;
  return <OrganizationDetail organizationId={organizationId} />;
}
