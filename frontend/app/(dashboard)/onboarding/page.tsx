import type { Metadata } from "next";

import { OnboardingPageClient } from "@/components/onboarding/onboarding-page";

export const metadata: Metadata = {
  title: "Getting started",
};

export default function OnboardingPage() {
  return <OnboardingPageClient />;
}
