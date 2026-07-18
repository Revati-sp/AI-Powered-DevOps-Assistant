#!/usr/bin/env sh
# Lightweight structural validation of Render Blueprint YAML files.
set -eu

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
failed=0

require_file() {
  path="$1"
  if [ ! -f "$path" ]; then
    echo "MISSING: $path" >&2
    failed=1
  else
    echo "OK: $path"
  fi
}

require_pattern() {
  path="$1"
  pattern="$2"
  label="$3"
  if ! grep -Eq "$pattern" "$path"; then
    echo "FAIL: $path missing ${label}" >&2
    failed=1
  else
    echo "OK: $path has ${label}"
  fi
}

for env in staging production; do
  file="${ROOT}/render.${env}.yaml"
  require_file "$file"
  require_pattern "$file" '^services:' "services"
  require_pattern "$file" '^databases:' "databases"
  require_pattern "$file" 'type:[[:space:]]*web' "web service"
  require_pattern "$file" 'type:[[:space:]]*worker' "worker service"
  require_pattern "$file" 'type:[[:space:]]*keyvalue' "keyvalue/redis"
  require_pattern "$file" 'preDeployCommand:' "preDeployCommand (migrations)"
  require_pattern "$file" 'healthCheckPath:' "healthCheckPath"
done

if [ "$failed" -ne 0 ]; then
  echo "Blueprint validation failed." >&2
  exit 1
fi

echo "All Render blueprints passed structural validation."
