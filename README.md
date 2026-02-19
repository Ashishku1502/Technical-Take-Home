# Technical Take-Home: Regression Lab (Django + DRF)

## Overview
This repository contains a Django/DRF service designed for a technical take-home assignment. It simulates a real-world scenario with an intentional regression bug, performance bottlenecks, and a requirement to add new features safely.

The project demonstrates:
- **Debugging & Regression Testing**: Identifying and fixing a critical bug where cancelling an order deleted the customer.
- **Performance Optimization**: solving N+1 query issues in summary endpoints using Django aggregation.
- **Feature Implementation**: Adding filtering capabilities to API endpoints.
- **System Design**: outlining a production-ready AWS architecture.

## Quick Start

### Prerequisites
- Python 3.10+

### Setup
1. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r regression_lab/requirements.txt
   ```

3. **Run migrations:**
   ```bash
   cd regression_lab
   python manage.py migrate
   ```

4. **Start the server:**
   ```bash
   python manage.py runserver
   ```
   Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

## Seeding Data
You can populate the database with sample data using the UI or the API.

**Option A (UI):** Click the `Seed sample data` button on the homepage.

**Option B (API):**
```bash
curl -X POST http://127.0.0.1:8000/api/dev/seed/ \
  -H "Content-Type: application/json" \
  -d '{"customers":200,"orders_per_customer":8,"items_per_order":4}'
```

## Running Tests
To verify the fixes and ensure no regressions:
```bash
cd regression_lab
python manage.py test
```
*Note: The test suite includes regression tests, feature tests, and performance benchmarks.*

## Solution Highlights

### 1. Regression Fix
- **Issue:** Cancelling an order triggered a signal that deleted the associated Customer.
- **Fix:** Removed the destructive `post_save` signal logic in `orders/signals.py`.
- **Verification:** Added `orders/tests/test_regression_bug.py` to ensure cancelling an order only updates the status.

### 2. Performance Improvement
- **Endpoint:** `GET /api/orders/summary/`
- **Optimization:** Replaced Python-level loops causing N+1 queries with efficient Django ORM aggregations (`annotate`, `Count`, `Sum`, `Coalesce`).
- **Result:** Reduced query count from ~60+ (depending on dataset) to exactly **1 query**, reducing response time from >1s to <10ms for large datasets.

### 3. New Feature: Order Filters
- Added support for filtering orders by status and customer email.
- **Usage:**
  - `GET /api/orders/?status=paid`
  - `GET /api/orders/?email=alice`

### 4. System Design
A proposed production architecture on AWS includes:
- **Compute:** AWS ECS (Fargate) for serverless container management.
- **Database:** Amazon RDS for PostgreSQL with PgBouncer for connection pooling.
- **Caching:** ElastiCache (Redis) for API response caching.
- **Async Tasks:** SQS + Celery for background processing.
- **Monitoring:** CloudWatch for p95 latency, error rates, and DB CPU utilization.

For full details, please refer to [SOLUTION.md](regression_lab/SOLUTION.md).
