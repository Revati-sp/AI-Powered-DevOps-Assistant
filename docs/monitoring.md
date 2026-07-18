# Monitoring

## Signals already in the app

| Signal | Source |
| --- | --- |
| API request volume / latency / status | Prometheus `/metrics` + request middleware |
| Rate-limit rejections | Prometheus counters |
| LLM latency / failures / circuit breaker | App metrics + OTEL hooks |
| Celery task duration / failures | Celery + worker logs / OTEL instrumentation |
| DB / Redis readiness | `/ready` |
| Frontend server errors | Next.js / Render logs |

Avoid high-cardinality metric labels (no raw user IDs, emails, or full routes with IDs). Route templates are used where possible.

## Production destination

Enable OpenTelemetry export to your collector (Grafana Cloud, Honeycomb, Datadog OTLP, etc.):

```text
OTEL_ENABLED=true
OTEL_SERVICE_NAME=ada-api-production   # distinct per service
OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp.example.com
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Bearer <secret>
OTEL_TRACES_SAMPLE_RATIO=0.1
LOG_FORMAT=json
```

Scrape Prometheus metrics from the API only from a private scraper or with:

```text
METRICS_ENABLED=true
METRICS_REQUIRE_AUTH=true
METRICS_ALLOWED_IPS=<scraper CIDRs or IPs>
```

Docs and OpenAPI are disabled in staging/production Blueprints.

## Structured logs

With `LOG_FORMAT=json`, API logs include:

```text
timestamp, level, service, environment, request_id, route, status, duration, error_category
```

`trace_id` is included when present on the log record (OTEL correlation).

### Never log

```text
passwords, tokens, cookies, API keys, prompts,
uploaded logs, artifact content, provider response bodies, database URLs
```

## Celery

Monitor:

- Queue depth (Redis / Celery inspect or provider dashboard)
- Task failures and retries
- Soft/hard time limit hits (`CELERY_TASK_SOFT_TIME_LIMIT_SECONDS` / `CELERY_TASK_TIME_LIMIT_SECONDS`)
- Worker process restarts (Render events)

Set `OTEL_SERVICE_NAME` distinctly for the worker service.

## Frontend

- Render HTTP logs for 5xx
- Synthetic smoke checks after deploy (`smoke_test.sh`)
- Optional uptime check on frontend `/` and API `/ready`

## Suggested alerts (starting set)

1. API `/ready` failing for >2 minutes
2. Elevated 5xx rate
3. Celery failure rate spike
4. Circuit breaker open for primary LLM
5. Migration / deploy failed (Render deploy event)
