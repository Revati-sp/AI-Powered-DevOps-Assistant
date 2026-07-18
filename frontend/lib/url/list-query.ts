export type ListQueryState = {
  page: number;
  search?: string;
  artifactType?: string;
  tag?: string;
  favoritesOnly: boolean;
  includeArchived: boolean;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
};
type SearchParamsLike = Pick<URLSearchParams, "get" | "toString">;

const asPositiveInt = (value: string | null, fallback: number) => {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
};

export function parseListQuery(searchParams: SearchParamsLike): ListQueryState {
  const sortOrder = searchParams.get("sort_order");
  return {
    page: asPositiveInt(searchParams.get("page"), 1),
    search: searchParams.get("search") || undefined,
    artifactType: searchParams.get("artifact_type") || undefined,
    tag: searchParams.get("tag") || undefined,
    favoritesOnly: searchParams.get("favorites_only") === "true",
    includeArchived: searchParams.get("include_archived") === "true",
    sortBy: searchParams.get("sort_by") || undefined,
    sortOrder: sortOrder === "asc" || sortOrder === "desc" ? sortOrder : undefined,
  };
}

/**
 * Merge a partial list-query update into the current URL params.
 * Only keys present on `state` are written; omitted keys are left unchanged.
 */
export function serializeListQuery(
  state: Partial<ListQueryState>,
  current: SearchParamsLike = new URLSearchParams(),
): string {
  const params = new URLSearchParams(current.toString());
  const write = (
    key: string,
    value: string | number | boolean | undefined,
    defaultValue?: string,
  ) => {
    if (value === undefined || value === false || value === "" || String(value) === defaultValue) {
      params.delete(key);
    } else {
      params.set(key, String(value));
    }
  };

  if ("page" in state) {
    write("page", state.page, "1");
  }
  if ("search" in state) {
    write("search", state.search);
  }
  if ("artifactType" in state) {
    write("artifact_type", state.artifactType);
  }
  if ("tag" in state) {
    write("tag", state.tag);
  }
  if ("favoritesOnly" in state) {
    write("favorites_only", state.favoritesOnly);
  }
  if ("includeArchived" in state) {
    write("include_archived", state.includeArchived);
  }
  if ("sortBy" in state) {
    write("sort_by", state.sortBy);
  }
  if ("sortOrder" in state) {
    write("sort_order", state.sortOrder);
  }
  return params.toString();
}
