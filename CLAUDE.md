# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**Redash** is a browser-based data query and visualization platform. It allows users to query data sources with SQL/NoSQL, create visualizations, build dashboards, set up alerts, and schedule query refreshes. The codebase has a Python/Flask backend, a React/TypeScript frontend, and a PostgreSQL database with Redis for caching and background job queues.

## Development Setup

### Prerequisites
- Docker and Docker Compose
- Node.js ≥18.0.0 and <26.0.0 (use `pnpm`)
- Python 3.8+

### Initial Setup

1. **Generate environment secrets:**
   ```bash
   make .env
   ```

2. **Start services (Redis + PostgreSQL):**
   ```bash
   make up
   ```

3. **Create the database:**
   ```bash
   make create_database
   ```

4. **Install frontend dependencies:**
   ```bash
   pnpm install --frozen-lockfile
   ```

### Running the Application

**Backend:**
- `docker compose run server runserver` — Start the Flask development server (inside Docker)
- Alternatively, run locally: `python manage.py runserver` (after pip installing dependencies)

**Frontend:**
- `pnpm start` — Starts webpack dev server + watches for client changes
- `pnpm build` — Production build
- `pnpm watch` — Watch mode without dev server

**Background Workers:**
- `docker compose run worker` — Start RQ worker for background jobs (emails, queries, alerts)
- `docker compose run scheduler` — Start periodic scheduler for recurring tasks

## Testing

### Backend Tests
```bash
make backend-unit-tests          # Full backend test suite + lint
make up test_db                  # Setup test database
docker compose run server tests  # Run tests only (after setup)
```

### Frontend Tests
```bash
pnpm test              # TypeScript type-check + Jest unit tests
pnpm test:watch        # Jest watch mode
pnpm run lint:fix      # Fix linting issues
pnpm run prettier      # Format code
```

### Code Quality
```bash
make lint              # Python linting (ruff + black)
make format            # Run pre-commit hooks
```

## Architecture

### Backend Structure

**Framework:** Flask with SQLAlchemy ORM

```
redash/
├── app.py                 # Flask app factory (create_app())
├── settings/              # Configuration (env vars, org settings)
├── models/                # SQLAlchemy ORM models (Query, Dashboard, etc.)
├── handlers/              # Flask request handlers (REST API)
│   ├── api.py            # Core API routes
│   ├── queries.py        # Query execution & results
│   ├── dashboards.py     # Dashboard operations
│   ├── alerts.py         # Alert notification handlers
│   └── email_csv.py      # CSV export endpoints
├── tasks/                 # Background jobs (RQ)
│   ├── general.py        # send_mail, record_event, etc.
│   ├── alerts.py         # Alert evaluation
│   ├── email_csv.py      # CSV generation & email
│   └── queries/          # Query execution tasks
├── query_runner/          # Data source connectors
├── destinations/          # Alert notification channels (Email, Slack, etc.)
├── authentication/        # User auth & SSO
├── serializers/          # JSON/CSV export logic
└── cli/                   # CLI commands (manage.py)
```

**Key Patterns:**

1. **Request Context in Background Jobs:** Background tasks (RQ workers) don't have Flask request context. Always wrap `mail.send()`, `current_app` usage, etc. with `app.app_context()`:
   ```python
   from redash.app import create_app
   app = create_app()
   with app.app_context():
       mail.send(message)
   ```

2. **Database Access:** Use `from redash.models import db` and work within Flask app context for transactions.

3. **Settings:** Organization-level settings use `org.get_setting()` / `org.set_setting()`. Global settings come from `redash.settings`.

### Frontend Structure

**Framework:** React 16 with TypeScript, compiled via Webpack

```
client/
├── app/
│   ├── components/       # Reusable React components
│   ├── pages/           # Page-level components (routed)
│   ├── services/        # API clients, utilities
│   ├── visualizations/  # Chart/viz components
│   ├── stores/          # State management
│   └── lib/             # Utility functions
└── cypress/             # E2E tests
```

**Styling:** Less/CSS with Bootstrap 3 foundation and Ant Design components.

### Background Jobs (RQ)

Jobs are decorated with `@job("queue_name")` and run in isolated worker processes:
- `"emails"` — Mail sending, notifications
- `"queries"` — Scheduled query execution
- `"default"` — General tasks (events, version checks)
- `"schemas"` — Data source schema refresh

**Important:** Job functions don't have Flask request context. Use `app.app_context()` for Flask operations.

### Data Source System

Query runners are plugins in `redash/query_runner/`. Each implements:
- `execute(query)` — Run the query, return results
- `test_connection()` — Validate data source connection
- `get_schema()` — Fetch table/column metadata

### Email & Alerts

**Email sending:**
- `redash.tasks.general.send_mail()` — Queued email task
- `redash.destinations.email.Email` — Alert notification via email

**Alerts:**
- Evaluated by `check_alerts_for_query()` background job
- Routed through `Destination` plugins (Email, Slack, Webhook, etc.)

## Code Style

**Python:**
- Auto-formatted with [Black](https://github.com/psf/black)
- Linted with [Ruff](https://github.com/astral-sh/ruff)
- Run `make lint` to check, `make format` to fix

**JavaScript/TypeScript:**
- Formatted with [Prettier](https://prettier.io/)
- Linted with [ESLint](https://eslint.org/)
- Run `pnpm run lint:fix` to auto-fix

## Database Migrations

Migrations use Flask-Migrate (Alembic):

```bash
# Generate migration after model changes:
docker compose run server create_migration "description"

# Apply migrations:
docker compose run server db upgrade
```

## Common Tasks

### Add a New API Endpoint
1. Create handler in `redash/handlers/` (inherit from `BaseResource`)
2. Register route in handler's `init_app()` or `redash/handlers/__init__.py`
3. Add tests in `tests/handlers/`
4. Update frontend client code in `client/app/services/`

### Add a Background Job
1. Define task in `redash/tasks/` with `@job()` decorator
2. Wrap Flask operations with `app.app_context()`
3. Queue via `task.delay(args)` from handlers or other tasks
4. Add tests mocking the task or using real Redis in test

### Add a New Data Source Connector
1. Create subclass of `BaseQueryRunner` in `redash/query_runner/`
2. Implement `execute()`, `test_connection()`, `get_schema()`
3. Register in `redash/query_runner/__init__.py`
4. Add icon and tests

### Modify Organization Settings
- Use `org.get_setting(key)` / `org.set_setting(key, value)`
- Settings are stored in the database and cached in Redis
- Access in handlers or tasks via the Organization model

## Important Notes

### Flask App Context
Background jobs and CLI commands need explicit app context for Flask features:
```python
from redash.app import create_app
app = create_app()
with app.app_context():
    # Now current_app, session, db operations work
```

### Database Sessions
- Use `db.session` for ORM operations
- Always `db.session.commit()` after writes
- Transactions auto-rollback on exception in request handlers

### Redis
- Primary: `redash.redis_connection` — caching, rate limiting, locks
- RQ: `redash.rq_redis_connection` — background job queue (different DB)

### Settings Override
Environment variables override config:
```bash
REDASH_MAIL_SERVER=smtp.example.com
REDASH_MAIL_PORT=587
REDASH_MAIL_USE_TLS=true
```

## Debugging

### Backend
- Set `DEBUG=true` to enable hot-reload and detailed errors
- View logs: `docker compose logs -f server`
- Use `docker compose run server bash` for interactive debugging

### Frontend
- Webpack dev server at http://localhost:8080 (or configured port)
- Browser DevTools work normally with sourcemaps
- Test in watch mode: `pnpm test:watch`

### Background Jobs
- View queues: `docker compose run --rm redis redis-cli -h redis`
- Check RQ dashboard (if enabled): http://localhost:9181
- Logs: `docker compose logs -f worker`

## Deployment

The project uses Docker for containerized deployment:
- `Dockerfile` builds the application image
- `compose.yaml` orchestrates local development
- Production deployments use Docker images tagged for releases

## Related Resources

- [Local Development Setup (Wiki)](https://github.com/getredash/redash/wiki/Local-development-setup)
- [User Documentation](https://redash.io/help/)
- [Contributing Guide](CONTRIBUTING.md)
- [GitHub Issues](https://github.com/getredash/redash/issues)
