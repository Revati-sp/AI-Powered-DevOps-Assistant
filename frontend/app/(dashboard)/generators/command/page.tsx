import type { Metadata } from "next";

import { CommandForm } from "@/components/generators/command-form";

export const metadata: Metadata = {
  title: "Shell Command Generator",
};

export default function CommandGeneratorPage() {
  return <CommandForm />;
}
