import { Badge } from "@/components/ui/badge";
import { LLM_PROVIDERS, type LlmProvider } from "@/lib/constants/app";
import { cn } from "@/lib/utils/cn";

const labels: Record<LlmProvider, string> = {
  gemini: "Gemini",
  llama: "Llama",
  mistral: "Mistral",
};

function normalizeProvider(provider: string): LlmProvider | null {
  return (LLM_PROVIDERS as readonly string[]).includes(provider) ? (provider as LlmProvider) : null;
}

export function ProviderBadge({ provider, className }: { provider: string; className?: string }) {
  const known = normalizeProvider(provider);
  const label = known ? labels[known] : provider;

  return (
    <Badge
      variant="secondary"
      className={cn("border-primary/20 bg-primary/10 text-primary capitalize", className)}
    >
      {label}
    </Badge>
  );
}
