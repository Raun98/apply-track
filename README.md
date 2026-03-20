# Job Application Tracking Board

An AI-powered job application tracking system that consolidates applications from multiple sources (LinkedIn, Naukri, Indeed) by parsing emails and automatically updating application statuses on a Kanban-style board.

## Features

- **Email Integration**: Connect existing Gmail/Outlook accounts via IMAP or use temporary mailbox forwarding
- **AI-Powered Parsing**: Claude API extracts job details from emails automatically
- **Kanban Board**: Drag-and-drop interface to manage application statuses
- **Multi-Source Support**: Recognizes emails from LinkedIn, Naukri, and Indeed
- **Real-time Updates**: WebSocket integration for live board updates
- **Dashboard**: Statistics on applications, response rates, and timeline views

## Tech Stack

- **Frontend**: React + TypeScript + Tailwind CSS + @dnd-kit (drag-and-drop)
- **Backend**: Python + FastAPI + SQLAlchemy + Alembic
- **Database**: PostgreSQL (primary) + Redis (caching/queues)
- **Email Processing**: IMAP (imap-tools) + Webhook endpoint
- **LLM Integration**: Claude API for email parsing
- **Job Queue**: Celery + Redis for async processing
- **Real-time**: WebSockets (FastAPI native)

## Project Structure

```
job-tracker/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── models/      # SQLAlchemy models
│   │   ├── services/    # Business logic (email parser, IMAP, etc.)
│   │   ├── tasks/       # Celery tasks
│   │   └── main.py      # FastAPI entry point
│   ├── alembic/         # Database migrations
│   └── requirements.txt
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── stores/      # Zustand state management
│   │   └── services/    # API clients
│   └── package.json
└── docker-compose.yml
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Anthropic API key (for email parsing)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd job-tracker
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Edit `.env` and add your Anthropic API key:
```bash
ANTHROPIC_API_KEY=sk-ant-...
```

4. Start all services:
```bash
docker-compose up -d
```

5. Run database migrations:
```bash
docker-compose exec backend alembic upgrade head
```

6. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api/v1
   - API Docs: http://localhost:8000/api/v1/docs

### Manual Setup (without Docker)

#### Backend

1. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export DATABASE_URL=postgresql://user:password@localhost:5432/jobtracker
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=your-secret-key
export ANTHROPIC_API_KEY=your-api-key
```

4. Run migrations:
```bash
alembic upgrade head
```

5. Start the server:
```bash
uvicorn app.main:app --reload
```

6. Start Celery worker (in another terminal):
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

7. Start Celery beat (for scheduled tasks):
```bash
celery -A app.tasks.celery_app beat --loglevel=info
```

#### Frontend

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm run dev
```

## Usage

### 1. Create an Account

Register a new account at http://localhost:3000/register

### 2. Connect Email (Optional)

- Go to "Email Settings" in the sidebar
- Add your Gmail/Outlook account with IMAP credentials
- Or use the temporary mailbox feature by forwarding emails to your unique address

### 3. Add Applications

- Click "Add Application" on the board
- Or let the system automatically create them from parsed emails

### 4. Manage Applications

- Drag and drop cards between columns to update status
- Click on cards to view/edit details
- View statistics on the Dashboard

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token

### Applications
- `GET /api/v1/applications` - List applications
- `POST /api/v1/applications` - Create application
- `GET /api/v1/applications/{id}` - Get application
- `PATCH /api/v1/applications/{id}` - Update application
- `DELETE /api/v1/applications/{id}` - Delete application

### Board
- `GET /api/v1/board/applications` - Get board data
- `POST /api/v1/board/cards/{id}/move` - Move card

### Email
- `GET /api/v1/email-accounts` - List email accounts
- `POST /api/v1/email-accounts` - Add email account
- `POST /api/v1/webhooks/email` - Receive forwarded emails

### WebSocket
- `ws://localhost:8000/api/v1/ws` - Real-time updates

## Email Processing Flow

### IMAP Flow
1. Celery Beat schedules periodic polling
2. IMAP service fetches new emails
3. Emails are queued to Celery
4. Claude API parses email content
5. Applications are created/updated
6. WebSocket broadcasts updates

### Webhook Flow
1. Email forwarded to user@tracker.app
2. POST /webhook/email receives the email
3. Email is queued to Celery
4. Same processing as IMAP flow

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | - |
| `SECRET_KEY` | JWT secret key | - |
| `ANTHROPIC_API_KEY` | Claude API key | - |
| `WEBHOOK_SECRET` | Webhook verification secret | - |
| `IMAP_POLL_INTERVAL_MINUTES` | IMAP polling interval | 5 |

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Database Migrations

```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## License

MIT
