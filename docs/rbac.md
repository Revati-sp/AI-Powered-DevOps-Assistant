# RBAC

Organizations are team workspaces. Each user has an organization role that grants a fixed set of permissions. Authorization is enforced in services via `OrganizationAuthService.require_permission`.

## Roles

| Role | Description |
|---|---|
| `owner` | Full access including organization delete |
| `admin` | Manage members, policies, audit; no org delete |
| `member` | Create resources, read/write artifacts, cancel own tasks |
| `viewer` | Read-only access to org metadata, artifacts, and policies |

Personal resources use `organization_id = null` and are scoped to the owning user.

## Permission matrix

Permissions are defined in `app/services/rbac.py` as the `Permission` enum.

| Permission | owner | admin | member | viewer |
|---|:---:|:---:|:---:|:---:|
| `organization.read` | ✓ | ✓ | ✓ | ✓ |
| `organization.update` | ✓ | ✓ | | |
| `organization.delete` | ✓ | | | |
| `member.manage` | ✓ | ✓ | | |
| `artifact.read` | ✓ | ✓ | ✓ | ✓ |
| `artifact.write` | ✓ | ✓ | ✓ | |
| `policy.read` | ✓ | ✓ | ✓ | ✓ |
| `policy.manage` | ✓ | ✓ | | |
| `audit.read` | ✓ | ✓ | | |
| `task.cancel` | ✓ | ✓ | ✓ | |
| `resource.create` | ✓ | ✓ | ✓ | |

## API usage

Organization routes under `/api/v1/organizations` and nested member routes check permissions before mutating state. Artifact, policy, audit, task, and org-scoped chat flows call `require_permission` with the relevant enum value.

Failed permission checks return HTTP `403` with code `FORBIDDEN`. Unknown or non-member organization access returns HTTP `404` with code `NOT_FOUND`.

## Owner protection

Business rules prevent removing or demoting the last owner of an organization (enforced in `OrganizationService`).
