# Policy packs

Organization policy packs apply deterministic, non-executable checks before and after LLM-assisted generation and reviews.

## Concepts

- **Policy pack**: named collection of rules for an organization; can be active or inactive.
- **Policy rule**: severity, resource type, and configuration that the policy engine evaluates.
- **Evaluation**: pure Python checks in `app/services/policy_engine.py` — no shell, no dynamic `eval`.

## Lifecycle

1. Create a pack for an organization (`POST /api/v1/organizations/{org_id}/policy-packs`).
2. Add rules (resource type, severity, configuration JSON).
3. Activate the pack.
4. Generator and review flows that are organization-scoped evaluate active packs and surface violations.

## Authorization

| Action | Owner | Admin | Member | Viewer |
|--------|-------|-------|--------|--------|
| Read packs/rules | yes | yes | yes | yes |
| Create/update/delete packs | yes | yes | no | no |
| Manage rules | yes | yes | no | no |

See [RBAC](rbac.md) for the full permission matrix.

## Safety properties

- Rule configuration size is bounded by application settings.
- Violations are returned as structured results; they do not execute user-supplied code.
- Audit events record policy management actions without storing full artifact bodies.

## Limitations

Policy packs are advisory gates for the MVP. They do not replace infrastructure scanners, admission controllers, or compliance certifications.
