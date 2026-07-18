#!/usr/bin/env sh
# Trigger a Render deploy for a service.
#
# Required env:
#   RENDER_API_KEY
#   RENDER_SERVICE_ID
# Optional:
#   IMAGE_URL    e.g. ghcr.io/org/ai-devops-backend@sha256:...
#                (requires the Render service to use runtime: image)
#   COMMIT_ID    git SHA to deploy for Dockerfile-based services
#   CLEAR_CACHE  true|false (default false)
set -eu

: "${RENDER_API_KEY:?RENDER_API_KEY is required}"
: "${RENDER_SERVICE_ID:?RENDER_SERVICE_ID is required}"

CLEAR_CACHE="${CLEAR_CACHE:-false}"

BODY=$(
  CLEAR_CACHE="$CLEAR_CACHE" IMAGE_URL="${IMAGE_URL:-}" COMMIT_ID="${COMMIT_ID:-}" python3 - <<'PY'
import json, os

payload = {
    "clearCache": "clear" if os.environ.get("CLEAR_CACHE") == "true" else "do_not_clear",
}
image_url = os.environ.get("IMAGE_URL", "").strip()
commit_id = os.environ.get("COMMIT_ID", "").strip()
if image_url:
    payload["imageUrl"] = image_url
if commit_id:
    payload["commitId"] = commit_id
print(json.dumps(payload))
PY
)

echo "Triggering Render deploy for service ${RENDER_SERVICE_ID}..."
RESP=$(curl -fsS -X POST \
  "https://api.render.com/v1/services/${RENDER_SERVICE_ID}/deploys" \
  -H "Authorization: Bearer ${RENDER_API_KEY}" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d "${BODY}")

echo "$RESP" | tee /tmp/render-deploy.json
echo "Deploy triggered."
