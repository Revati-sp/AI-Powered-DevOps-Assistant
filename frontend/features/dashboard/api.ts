import type { JobStatus } from "@/components/data-display/status-badge";
import { listConversations } from "@/features/chat/api";
import type { ConversationListItem } from "@/features/chat/types";
import { apiFetch } from "@/lib/api/client";
import { endpoints } from "@/lib/api/endpoints";
import type { components } from "@/lib/api/generated-types";

type ArtifactsPage = components["schemas"]["Page_ArtifactSummaryResponse_"];
type TasksPage = components["schemas"]["Page_TaskSummaryResponse_"];
type OrgsPage = components["schemas"]["Page_OrganizationResponse_"];
type ArtifactSummary = components["schemas"]["ArtifactSummaryResponse"];
type TaskSummary = components["schemas"]["TaskSummaryResponse"];
type Organization = components["schemas"]["OrganizationResponse"];

export type DashboardActivityItem = {
  id: string;
  kind: "conversation" | "artifact" | "task";
  title: string;
  subtitle: string;
  href: string;
  at: string;
};

export type TaskStatusCounts = Record<JobStatus, number>;

export type DashboardSnapshot = {
  conversations: ConversationListItem[];
  artifacts: ArtifactSummary[];
  tasks: TaskSummary[];
  organizations: Organization[];
  recentActivity: DashboardActivityItem[];
  taskStatusCounts: TaskStatusCounts;
  totals: {
    conversations: number;
    artifacts: number;
    tasks: number;
    organizations: number;
  };
  memberCount: null;
  failures: {
    conversations: boolean;
    artifacts: boolean;
    tasks: boolean;
    organizations: boolean;
  };
};

const EMPTY_STATUS_COUNTS: TaskStatusCounts = {
  queued: 0,
  running: 0,
  succeeded: 0,
  failed: 0,
  cancelled: 0,
};

function settledValue<T>(result: PromiseSettledResult<T>, fallback: T): T {
  return result.status === "fulfilled" ? result.value : fallback;
}

function countTaskStatuses(tasks: TaskSummary[]): TaskStatusCounts {
  const counts = { ...EMPTY_STATUS_COUNTS };
  for (const task of tasks) {
    if (task.status in counts) {
      counts[task.status as JobStatus] += 1;
    }
  }
  return counts;
}

function buildRecentActivity(
  conversations: ConversationListItem[],
  artifacts: ArtifactSummary[],
  tasks: TaskSummary[],
): DashboardActivityItem[] {
  const items: DashboardActivityItem[] = [
    ...conversations.map((item) => ({
      id: `conversation-${item.id}`,
      kind: "conversation" as const,
      title: item.title || "Untitled chat",
      subtitle: `Chat · ${item.provider}`,
      href: `/chat/${item.id}`,
      at: item.updatedAt,
    })),
    ...artifacts.map((item) => ({
      id: `artifact-${item.id}`,
      kind: "artifact" as const,
      title: item.name,
      subtitle: `Artifact · ${item.artifact_type}`,
      href: `/artifacts/${item.id}`,
      at: item.updated_at,
    })),
    ...tasks.map((item) => ({
      id: `task-${item.id}`,
      kind: "task" as const,
      title: item.task_type,
      subtitle: `Task · ${item.status}`,
      href: `/tasks`,
      at: item.completed_at ?? item.started_at ?? item.created_at,
    })),
  ];

  return items.sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime()).slice(0, 8);
}

export async function fetchDashboardSnapshot(): Promise<DashboardSnapshot> {
  const [conversationsResult, artifactsResult, tasksResult, orgsResult] = await Promise.allSettled([
    listConversations(),
    apiFetch<ArtifactsPage>(`${endpoints.artifacts.list()}?limit=5&offset=0`),
    apiFetch<TasksPage>(`${endpoints.tasks.list()}?limit=20&offset=0`),
    apiFetch<OrgsPage>(`${endpoints.organizations.list()}?limit=5&offset=0`),
  ]);

  const conversations = settledValue(conversationsResult, []).slice(0, 5);
  const artifactsPage = settledValue(artifactsResult, {
    items: [],
    total: 0,
    limit: 5,
    offset: 0,
  });
  const tasksPage = settledValue(tasksResult, {
    items: [],
    total: 0,
    limit: 20,
    offset: 0,
  });
  const orgsPage = settledValue(orgsResult, {
    items: [],
    total: 0,
    limit: 5,
    offset: 0,
  });

  const artifacts = artifactsPage.items;
  const tasks = tasksPage.items;
  const organizations = orgsPage.items;

  return {
    conversations,
    artifacts,
    tasks,
    organizations,
    recentActivity: buildRecentActivity(conversations, artifacts, tasks),
    taskStatusCounts: countTaskStatuses(tasks),
    totals: {
      conversations:
        conversationsResult.status === "fulfilled"
          ? conversationsResult.value.length
          : conversations.length,
      artifacts: artifactsPage.total,
      tasks: tasksPage.total,
      organizations: orgsPage.total,
    },
    memberCount: null,
    failures: {
      conversations: conversationsResult.status === "rejected",
      artifacts: artifactsResult.status === "rejected",
      tasks: tasksResult.status === "rejected",
      organizations: orgsResult.status === "rejected",
    },
  };
}
