# ApplyTrack

AI-powered job application tracker. Connect your email or forward job-related emails, and ApplyTrack automatically parses them, creates application cards, and updates your Kanban board in real time.

## Features

- Kanban board with drag-and-drop status tracking
- AI email parsing (Claude / Ollama / regex fallback)
- IMAP polling and webhook-based email ingestion
- Razorpay subscription billing
- Real-time WebSocket updates
- Mobile-responsive layout

## Quick Start (Docker)

```bash
cp .env.example .env
# Edit .env with your keys
docker compose up --build
```

- Frontend: http://localhost
- Backend API: http://localhost:8000/api/v1
- API docs: http://localhost:8000/docs

## Deployment (Railway)

### Required Environment Variables

| Variable | Description | How to generate |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | Railway provides this automatically |
| `REDIS_URL` | Redis connection string | Railway provides this automatically |
| `SECRET_KEY` | JWT signing key | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ENCRYPTION_KEY` | Fernet key for IMAP password encryption | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `FRONTEND_URL` | Your frontend URL (e.g. `https://your-app.up.railway.app`) | Set after deploy |
| `CORS_ORIGINS` | Comma-separated allowed origins | Same as FRONTEND_URL |
| `ANTHROPIC_API_KEY` | Claude API key for email parsing | From console.anthropic.com |
| `RAZORPAY_KEY_ID` | Razorpay key ID (for paid plans) | From Razorpay dashboard |
| `RAZORPAY_KEY_SECRET` | Razorpay key secret | From Razorpay dashboard |
| `RAZORPAY_WEBHOOK_SECRET` | Razorpay webhook signing secret | From Razorpay webhook settings |
| `MAILGUN_API_KEY` | Mailgun API key (for transactional email) | From Mailgun dashboard |
| `MAILGUN_DOMAIN` | Mailgun sending domain | From Mailgun dashboard |
| `ADMIN_SECRET` | Secret header for admin endpoints | Any strong random string |
| `VITE_API_BASE_URL` | Backend API URL for the frontend build | e.g. `https://your-backend.up.railway.app/api/v1` |

### Steps

1. **Fork** this repository.
2. **Connect Railway** — create a new project, link your fork, and add PostgreSQL + Redis services.
3. **Set environment variables** — add all required vars listed above in the Railway service settings.
4. **Deploy** — Railway will build and deploy automatically.
5. **Run migrations** post-deploy:
   ```bash
   railway run alembic upgrade head
   ```
6. **Generate keys** if you haven't already:
   ```bash
   # SECRET_KEY
   python -c "import secrets; print(secrets.token_hex(32))"
   # ENCRYPTION_KEY
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

### Razorpay Plan Seeding

After setting `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, and `ADMIN_SECRET`, seed the plans:

```bash
curl -X POST https://your-backend.up.railway.app/api/v1/admin/seed-razorpay-plans \
  -H "X-Admin-Secret: your-admin-secret"
```

This creates Razorpay plans for Pro and Premium tiers and stores the plan IDs in the database. Safe to call multiple times.

### Mailgun Inbound Email Setup

To enable email forwarding (users forward job emails to `user{id}@inbox.applytrack.app`):

1. Set up your domain in **Mailgun** (e.g. `inbox.applytrack.app`).
2. Add MX records as directed by Mailgun.
3. Create a **Route** in Mailgun:
   - Filter: `match_recipient("user\d+@inbox.applytrack.app")`
   - Action: `forward("https://your-railway-url/api/v1/webhooks/mailgun-inbound")`
4. Set `MAILGUN_API_KEY` and `MAILGUN_DOMAIN` in your environment for signature verification and outbound email (password reset, verification).

## Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## License

MIT
