export type SessionResponse = {
  id: string;
  created_at: string;
  expires_at: string;
  revoked: boolean;
  approx_ip: string | null;
  approx_client: string | null;
  is_current: boolean;
};

export type ForgotPasswordResponse = {
  message: string;
};

export type InvitationAcceptResponse = {
  organization_id: string;
  organization_name: string;
  role: string;
  message?: string;
};
