import type { Metadata } from "next";

import { ReviewWorkspace } from "@/components/reviews/review-workspace";

export const metadata: Metadata = {
  title: "Configuration Review",
};

export default function ReviewsPage() {
  return <ReviewWorkspace />;
}
