import type { Metadata } from "next";

import { MembersPageClient } from "@/components/organizations/members-page";

export const metadata: Metadata = {
  title: "Members",
};

type Props = {
  params: Promise<{ organizationId: string }>;
};

export default async function MembersPage({ params }: Props) {
  const { organizationId } = await params;
  return <MembersPageClient organizationId={organizationId} />;
}
