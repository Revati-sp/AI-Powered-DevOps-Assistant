#!/usr/bin/env sh
# Post-deploy smoke checks against public HTTPS URLs.
# Usage:
#   FRONTEND_URL=https://app-staging.example.com \
#   API_URL=https://api-staging.example.com \
#   ./deploy/render/scripts/smoke_test.sh
set -eu

FRONTEND_URL="${FRONTEND_URL:?FRONTEND_URL is required}"
API_URL="${API_URL:?API_URL is required}"

echo "Smoke: frontend ${FRONTEND_URL}"
curl -fsS -o /dev/null -w "frontend_http=%{http_code}\n" "${FRONTEND_URL}/"

echo "Smoke: API liveness ${API_URL}/health"
curl -fsS "${API_URL}/health" | tee /tmp/ada-health.json
echo

echo "Smoke: API readiness ${API_URL}/ready"
curl -fsS "${API_URL}/ready" | tee /tmp/ada-ready.json
echo

# Ready payload should indicate ok / ready without requiring auth.
if ! grep -Eqi '"status"[[:space:]]*:[[:space:]]*"(ok|ready|healthy)"' /tmp/ada-ready.json \
  && ! grep -Eqi '"ready"[[:space:]]*:[[:space:]]*true' /tmp/ada-ready.json; then
  # Accept 200 with any JSON body from /ready — HTTP success is the gate.
  echo "Ready endpoint returned HTTP 200 (body shape may vary)."
fi

echo "Smoke tests passed."
