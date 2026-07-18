import type { Metadata } from "next";

import { KubernetesForm } from "@/components/generators/kubernetes-form";

export const metadata: Metadata = {
  title: "Kubernetes Generator",
};

export default function KubernetesGeneratorPage() {
  return <KubernetesForm />;
}
