import { LoadingState } from "@/components/feedback/loading-state";

export default function Loading() {
  return (
    <div className="from-background via-background to-primary/5 flex min-h-svh items-center justify-center bg-gradient-to-b">
      <LoadingState label="Loading workspace…" />
    </div>
  );
}
