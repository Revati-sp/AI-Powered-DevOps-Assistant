import type { Metadata } from "next";

import { PipelineForm } from "@/components/generators/pipeline-form";

export const metadata: Metadata = {
  title: "CI/CD Pipeline Generator",
};

export default function PipelineGeneratorPage() {
  return <PipelineForm />;
}
