import type { Metadata } from "next";

import { OrganizationsPageClient } from "@/components/organizations/organizations-page";

export const metadata: Metadata = {
  title: "Organizations",
};

export default function OrganizationsPage() {
  return <OrganizationsPageClient />;
}
