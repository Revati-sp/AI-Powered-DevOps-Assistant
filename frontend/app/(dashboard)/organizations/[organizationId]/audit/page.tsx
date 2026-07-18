import type { Metadata } from "next";

import { AuditPageClient } from "@/components/audit/audit-page";

export const metadata: Metadata = {
  title: "Audit log",
};

type Props = {
  params: Promise<{ organizationId: string }>;
};

export default async function AuditPage({ params }: Props) {
  const { organizationId } = await params;
  return <AuditPageClient organizationId={organizationId} />;
}
