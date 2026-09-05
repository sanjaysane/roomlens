# Scale & performance — measured, not modeled

> Every number below was measured on 2026-09-05 against the actual app.
> Nothing here is projected, extrapolated, or "expected".

## Load test setup

- **Target**: FastAPI app (`uvicorn`, **single worker**, defaults) on this Linux VM,
  backed by real PostgreSQL 16 (local socket, schema applied).
- **Workload**: `locustfile.py` — Meta-shaped webhook traffic:
  70% text messages (welcome → role pick → single-digit replies, incl. `STOP`),
  20% image messages (room-photo path), 10% `GET /health` probes.
- **Profile**: 50 concurrent users, 10 users/s ramp, **2 minutes**.

## Measured results (50 users, 2 min, single worker)

| Endpoint | Requests | Failures | Throughput | Avg | Median (p50) | p95 | p99 | Max |
|---|---|---|---|---|---|---|---|---|
| `POST /webhook` | 4,183 | **0** | ~35 req/s | 576 ms | 480 ms | 1,200 ms | 2,200 ms | 8,728 ms |
| `GET /health` | 479 | **0** | ~4 req/s | 1,542 ms | 1,500 ms | 3,100 ms | 4,200 ms | 4,645 ms |

- **Error rate: 0.00%** across 4,662 requests.
- Each webhook request does a full stateless round trip: parse the nested Meta
  payload, hydrate the chat session from PostgreSQL, dispatch the state machine,
  and persist the reply — no caching, no session affinity.

## What the numbers mean

1. **A single worker handles ~35 webhook req/s with zero errors.** For a
   WhatsApp conversational workload (bursty, human-paced), that is a healthy
   baseline — one studio's traffic fits comfortably.
2. **`/health` p50 of 1.5 s is queueing, not work.** The endpoint returns a
   constant JSON body with no DB access. Under load it waits behind webhook
   POSTs on the single worker. If your orchestrator is health-check sensitive,
   run multiple workers — the app is stateless and scales horizontally.
3. **Webhook p50 of 480 ms is dominated by per-request DB connections**
   (each DB call opens a fresh connection; no pool yet). A connection pool
   (e.g. PgBouncer or psycopg pool) is the obvious next optimization.

## Reproduce it

```bash
# terminal 1 — app with a real database
DATABASE_URL=postgresql://roomlens:roomlens@localhost:5432/roomlens \
  uvicorn src.main:app --port 8000

# terminal 2 — load
locust -f locustfile.py --headless -u 50 -r 10 -t 2m \
  --host http://127.0.0.1:8000
```

A manual-load workflow (`.github/workflows/loadtest.yml`) runs the same
profile in CI against the compose stack and uploads the HTML report.

## Honest limits

- Not tested: 200+ concurrent users, multi-worker uvicorn, pooled DB,
  Gunicorn, or production Meta webhook volume. Don't quote those.
- The composite/render path (Pillow + ffmpeg) was not the bottleneck here;
  it will be if many visualizations render concurrently — pre-warm or queue
  renders if a studio batch-imports.
