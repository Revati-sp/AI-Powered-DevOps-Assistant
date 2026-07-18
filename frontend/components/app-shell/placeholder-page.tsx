import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

import { PageHeader } from "@/components/data-display/page-header";
import { EmptyState } from "@/components/feedback/empty-state";

type PlaceholderPageProps = {
  title: string;
  description: string;
  emptyTitle: string;
  emptyDescription: string;
  icon: LucideIcon;
  actions?: ReactNode;
};

export function PlaceholderPage({
  title,
  description,
  emptyTitle,
  emptyDescription,
  icon: Icon,
  actions,
}: PlaceholderPageProps) {
  return (
    <div className="space-y-6">
      <PageHeader title={title} description={description} actions={actions} />
      <EmptyState icon={<Icon />} title={emptyTitle} description={emptyDescription} />
    </div>
  );
}
