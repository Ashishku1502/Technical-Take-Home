# Solution

## Mental Model
The service manages Customers, Orders, and OrderItems. The original implementation had significant performance bottlenecks due to N+1 query patterns and a critical instability where business logic (cancelling orders) had destructive side-effects on parent records (deleting customers).

## Instability
**Regression**: Cancelling an order deleted the associated Customer, which would cascade verify delete all other orders for that customer.
**Reproduction**: 
`POST /api/orders/<id>/cancel/` -> check if Customer exists.
**Root Cause**: A `post_save` signal in `orders/signals.py` explicitly called `instance.customer.delete()` when functionality was `CANCELLED`.
**Fix**: Removed the destructive logic in the signal.
**Prevention**: Use strict code review for signals. Avoid side-effects in signals that affect parent relationships. Add rigorous regression tests for state transitions.

## Feature: Order Filters
Added filtering to `GET /api/orders/`:
- `status`: Exact match (e.g., `?status=paid`).
- `email`: Case-insensitive containment (e.g., `?email=alice`).
- Implemented in `OrderViewSet.get_queryset`.
- Added tests in `orders/tests/test_feature_filters.py`.

## Performance
**Summary Endpoint (`GET /api/orders/summary/`)**
- **Issue**: Nested loops causing N+1 queries (N customers * M orders * K items).
- **Fix**: Replaced loops with a single Django aggregation query using `annotate`, `Count`, and `Sum` wrapped in `Coalesce` for robust sorting of NULL values (zero spenders).
- **Evidence**:
  - Before: ~61 queries (small dataset), >1s for large datasets.
  - After: 1 query. <10ms.

**Seed Endpoint (`POST /api/dev/seed/`)**
- **Issue**: `OrderItem.save()` triggered a recalculation of Order totals, causing N extra queries per item + commit overhead.
- **Fix**: 
  - Wrapped in `transaction.atomic()` to group commits.
  - Used `bulk_create` for items to bypass `save()` signal.
  - Manually calculated and updated `Order.total_cents` in bulk.
- **Evidence**:
  - Before: ~511 queries for (10 customers, 5 orders, 3 items).
  - After: 163 queries.
  - Time: Reduced from ~0.8s to ~0.13s.

## Tests
- `orders/tests/test_regression_bug.py`: Verifies customer and other orders preservation.
- `orders/tests/test_feature_filters.py`: Verifies status and email filtering.
- `orders/tests/test_performance.py`: Verifies query counts for seed and summary endpoints.
- `orders/tests/test_sorting.py`: Verifies summary endpoint sorts zero-spenders (NULL totals) correctly.

## AWS Production Readiness
- **Runtime**: **AWS ECS (Fargate)**.
  - *Why*: Serverless container management reduces ops overhead compared to EC2. Easier to scale than App Runner for complex networking.
- **Database**: **Amazon RDS for PostgreSQL**.
  - *Considerations*: Use **PgBouncer** for connection pooling, as Django creates a connection per request which can exhaust database connections under load.
- **Caching/Queue**: 
  - **ElastiCache (Redis)** for caching API responses (summary endpoint) and session storage.
  - **SQS + Celery** for async tasks (e.g., sending emails, generating heavy reports, seeding).
- **CI/CD**:
  - GitHub Actions to run tests.
  - Build Docker image -> Push to ECR.
  - Update ECS Service (blue/green deployment).
- **Metrics/Alerts (Day 1)**:
  1. HTTP 5xx Error Rate (> 1%).
  2. p95 and p99 Latency (> 500ms).
  3. Database CPU Utilization (> 80%).
  4. Database Connection Count (approaching limit).
  5. SQS Queue Depth (backlog).
  6. Disk Space (Log/DB).

## Risks & Tradeoffs
- **Tradeoff**: `Order.total_cents` is a denormalized field.
  - *Risk*: Data inconsistency if an item is updated without updating the order (e.g., raw SQL or `bulk_create` without manual sync).
  - *Mitigation*: Periodic background job to reconcile totals, or database triggers (complex).
- **Seed Concurrency**: The seed endpoint uses deterministic email generation which will fail with IntegrityError if run concurrently. Accepted as it's a dev tool.

## AI Usage
- Used AI assistant to scan codebase for N+1 patterns.
- Generated the optimized Django aggregation query syntax.
- Drafted initial unit tests for regression verification.
