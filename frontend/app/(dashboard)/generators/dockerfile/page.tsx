import type { Metadata } from "next";

import { DockerfileForm } from "@/components/generators/dockerfile-form";

export const metadata: Metadata = {
  title: "Dockerfile Generator",
};

export default function DockerfileGeneratorPage() {
  return <DockerfileForm />;
}
