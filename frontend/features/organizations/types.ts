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

export type InvitationStatus = "pending" | "accepted" | "declined" | "revoked" | "expired";

export type InvitationResponse = {
  id: string;
  organization_id: string;
  email: string;
  role: OrgRole;
  status: InvitationStatus;
  invited_by_user_id: string;
  expires_at: string;
  accepted_at: string | null;
  declined_at: string | null;
  revoked_at: string | null;
  created_at: string;
};

export type InvitationsPage = {
  items: InvitationResponse[];
  total: number;
  limit: number;
  offset: number;
};

export type CreateInvitationRequest = {
  email: string;
  role: OrgRole;
};
