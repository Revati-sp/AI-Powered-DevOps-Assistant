import type { components } from "@/lib/api/generated-types";

export type OrganizationResponse = components["schemas"]["OrganizationResponse"];
export type OrganizationCreate = components["schemas"]["OrganizationCreate"];
export type OrganizationUpdate = components["schemas"]["OrganizationUpdate"];
export type OrganizationsPage = components["schemas"]["Page_OrganizationResponse_"];
export type OrganizationMemberResponse = components["schemas"]["OrganizationMemberResponse"];
export type MembersPage = components["schemas"]["Page_OrganizationMemberResponse_"];
export type AddMemberRequest = components["schemas"]["AddMemberRequest"];
export type UpdateMemberRequest = components["schemas"]["UpdateMemberRequest"];
export type OrgRole = components["schemas"]["OrgRole"];
