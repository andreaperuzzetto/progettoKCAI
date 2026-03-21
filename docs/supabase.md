# Supabase Setup Guide

This project uses Supabase as the managed PostgreSQL database. Since the backend uses standard SQLAlchemy, only the connection string needs to be configured — no Supabase SDK or client libraries are required.

---

## 1. Get Your Connection String

1. Open [app.supabase.com](https://app.supabase.com) and select your project
2. Go to **Project Settings → Database**
3. Scroll to **Connection string**
4. Select the **URI** tab
5. Choose **Session mode** (port `5432`) — recommended for SQLAlchemy

The string will look like:
```
postgresql://postgres.[project-ref]:[your-password]@aws-0-[region].pooler.supabase.com:5432/postgres
```

> **Note:** Replace `[your-password]` with your actual database password. The password is NOT shown pre-filled; you set it when you created the project. If you forgot it, reset it under **Project Settings → Database → Reset database password**.

---

## 2. Configure the `.env` File

Copy the example file and fill in your connection string:

```bash
cp .env.example .env
```

Edit `.env`:
```env
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
SECRET_KEY=your-random-secret-key-min-32-chars
```

The SSL connection is handled automatically — the backend detects non-local PostgreSQL connections and enables `sslmode=require`.

---

## 3. Start the Backend

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload
```

On first startup, SQLAlchemy will run `CREATE TABLE IF NOT EXISTS` for all models automatically. You can verify the tables were created in the Supabase Dashboard under **Table Editor**.

---

## 4. Verify the Connection

```bash
curl http://localhost:8000/health
# Expected: {"status": "ok"}
```

Or check the Supabase Dashboard → **Table Editor** — you should see all tables listed after the first startup.

---

## Connection Pooler Options

Supabase offers three connection options. Use **Session pooler** for this project:

| Mode | Port | Use case |
|------|------|---------|
| Direct connection | `5432` (host: `db.[ref].supabase.co`) | Low-traffic / dev only |
| **Session pooler** | `5432` (host: `*.pooler.supabase.com`) | ✅ FastAPI / SQLAlchemy (recommended) |
| Transaction pooler | `6543` (host: `*.pooler.supabase.com`) | Serverless functions (edge) |

> **Why not Transaction pooler?** PgBouncer in transaction mode doesn't support prepared statements, which SQLAlchemy uses by default. Session pooler is functionally equivalent to a direct connection for this use case.

---

## Environment Variables Set by the Backend

All connection pool settings are managed in `backend/db/database.py`:

| Setting | Value | Purpose |
|---------|-------|---------|
| `pool_size` | 5 | Persistent connections kept open |
| `max_overflow` | 10 | Extra connections under load |
| `pool_timeout` | 30s | Max wait for a connection |
| `pool_recycle` | 1800s | Reconnect idle connections every 30 min |
| `pool_pre_ping` | True | Test connection health before use |

---

## Troubleshooting

**`connection refused` or `timeout`**  
→ Check that the `DATABASE_URL` host and port are correct. Use the Session pooler string, not the Direct connection string (the direct host starts with `db.`, the pooler host starts with `aws-0-`).

**`SSL connection is required`**  
→ Add `?sslmode=require` to the end of your `DATABASE_URL`. The backend adds this automatically for non-local hosts, but it can be explicit too.

**`password authentication failed`**  
→ The password in the connection string is URL-encoded. If your password contains special characters (e.g. `@`, `#`, `/`), they must be percent-encoded. The safest fix is to reset the DB password to something without special characters via **Project Settings → Database → Reset database password**.

**Tables not created after startup**  
→ Check the uvicorn logs for SQLAlchemy errors. The most common cause is an incorrect `DATABASE_URL`.
