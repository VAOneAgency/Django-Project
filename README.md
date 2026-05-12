# OnePulse Social Publisher

![OnePulse Social Publisher](https://vaoneagency.com/wp-content/uploads/2026/05/Screenshot-2026-05-12-192253.png)

A multi-platform social media management tool built with Django. OnePulse lets teams schedule, publish, and track posts across Instagram, Facebook, Twitter/X, LinkedIn, and TikTok — all from a single dashboard organized by client organization.

**Live App:** [http://social.onepulsecrm.com](http://social.onepulsecrm.com)

---

## Features

- **Multi-organization support** — manage social accounts for multiple clients or brands under one login
- **Platform connections** — connect Instagram Business, Facebook Pages, Twitter/X, LinkedIn, and TikTok accounts
- **Post scheduling** — draft, schedule, or immediately publish posts with caption and media
- **Post analytics** — track per-platform publish status, errors, and engagement data
- **Role-based access control** — assign staff to roles with granular permissions (manage accounts, edit/delete posts)
- **Webhook support** — receive and log Meta webhook events for real-time Instagram/Facebook updates
- **Staff management** — admin users can create and manage staff accounts with secure password hashing
- **Session-based authentication** — Django's built-in auth with a custom Staff user model

---

## Screenshots

| Dashboard | Scheduled Post | Connect Account |
|-----------|----------------|-----------------|
| [![Dashboard](https://vaoneagency.com/wp-content/uploads/2026/05/Screenshot-2026-05-12-192253.png)](https://vaoneagency.com/wp-content/uploads/2026/05/Screenshot-2026-05-12-192253.png) | [![Scheduled Post](https://vaoneagency.com/wp-content/uploads/2026/05/Screenshot-2026-05-12-192305.png)](https://vaoneagency.com/wp-content/uploads/2026/05/Screenshot-2026-05-12-192305.png) | [![Connect Accounts](https://vaoneagency.com/wp-content/uploads/2026/05/Screenshot-2026-05-12-192317.png)](https://vaoneagency.com/wp-content/uploads/2026/05/Screenshot-2026-05-12-192317.png) |

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- pip / pipenv

### Local Setup

1. **Clone the repository**

```bash
git clone https://github.com/VAOneAgency/Django-Project.git
cd Django-Project.git
```

2. **Create and activate a virtual environment**

```bash
python3.11 -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Create a PostgreSQL database**

```bash
psql -U postgres
CREATE DATABASE onepulse_db;
CREATE USER onepulse_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE onepulse_db TO onepulse_user;
\q
```

5. **Configure environment variables**

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=postgresql://onepulse_user:yourpassword@localhost:5432/onepulse_db
WEBHOOK_VERIFY_TOKEN=your_webhook_token
```

Generate a secret key:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

6. **Run migrations and create a superuser**

```bash
python manage.py migrate
python manage.py createsuperuser
```

7. **Collect static files and start the dev server**

```bash
python manage.py collectstatic --noinput
python manage.py runserver
```

Visit [http://localhost:8000/login/](http://localhost:8000/login/) to log in.

---

## Planning Materials

- [ERD / Data Model Diagram](#) ← add link
- [Wireframes / Trello Board](#) ← add link

---

## Data Models

| Model | Description |
|-------|-------------|
| `Staff` | Custom user model extending `AbstractUser`. Has `is_admin` flag synced to `is_staff`. |
| `Organization` | A client or brand. Staff are assigned to organizations via roles. |
| `Role` | Named permission set (e.g. Editor, Viewer). Supports system roles. |
| `StaffRoleAssignment` | Many-to-many relationship between Staff and Role. |
| `RolePermission` | Granular permissions attached to a Role. |
| `SocialAccount` | A connected platform account (Instagram, Facebook, etc.) belonging to an Organization. Stores access tokens, app credentials, and connection status. |
| `Post` | A piece of content with caption, status (draft/scheduled/published), and scheduled time. Belongs to an Organization and created_by Staff. |
| `PostPlatform` | Junction table — tracks publish status per platform for each Post. |
| `PostImage` | Images attached to a Post, with sort order and media type. |
| `WebhookEvent` | Logs incoming Meta webhook payloads for auditing and debugging. |

---

## Technologies Used

- **Python 3.11**
- **Django 5.x** — web framework, ORM, session auth, admin
- **PostgreSQL 14** — primary database
- **psycopg2-binary** — PostgreSQL adapter
- **dj-database-url** — parses `DATABASE_URL` for database config
- **WhiteNoise** — serves static files in production without a CDN
- **Gunicorn** — WSGI server for production deployment
- **python-dotenv** — loads `.env` variables
- **Meta Graph API** — Instagram and Facebook publishing
- **CSS Custom Properties + Flexbox/Grid** — responsive layout system

---

## Deployment

This app is deployed on a VPS (Bluehost) running AlmaLinux with:

- **Gunicorn** managed by `systemd`
- **Apache** with `mod_proxy` reverse proxying to the Gunicorn Unix socket
- **PostgreSQL 14** on port 5433
- **cPanel** for domain/DNS management

### Production Environment Variables

```env
SECRET_KEY=<strong-random-key>
DEBUG=False
DATABASE_URL=postgresql://user:password@localhost:5433/onepulse_social
WEBHOOK_VERIFY_TOKEN=<your-meta-webhook-token>
ALLOWED_HOSTS=social.onepulsecrm.com
```

### Redeploy Steps

```bash
cd /home/vaoneagencyop/public_html/social
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart social_onepulse
```

---

## Meta Webhook Setup

To receive real-time Instagram/Facebook events:

1. Go to [Meta Developer Dashboard](https://developers.facebook.com)
2. Navigate to your App → Use Cases → Instagram → API Setup → Configure Webhooks
3. Set the callback URL to: `https://social.onepulsecrm.com/webhooks/meta/`
4. Set the Verify Token to match `WEBHOOK_VERIFY_TOKEN` in your `.env`
5. Subscribe to: `mentions`, `comments`, `messages`

---

## Attributions

- [Django](https://www.djangoproject.com/) — BSD License
- [WhiteNoise](http://whitenoise.evans.io/) — MIT License
- [dj-database-url](https://github.com/jazzband/dj-database-url) — BSD License
- [Cormorant Garamond](https://fonts.google.com/specimen/Cormorant+Garamond) — Google Fonts (SIL Open Font License)
- [Meta Graph API](https://developers.facebook.com/docs/graph-api/) — Meta Platform Terms

---

## Next Steps

- [ ] OAuth 2.0 flow for Instagram and Facebook (replace manual token entry)
- [ ] Twitter/X OAuth 2.0 integration via `tweepy`
- [ ] LinkedIn and TikTok API publishing
- [ ] Image upload UI with drag-and-drop ordering
- [ ] Post performance analytics dashboard (impressions, reach, engagement)
- [ ] Bulk scheduling via CSV import
- [ ] Client-facing read-only reporting portal
- [ ] Email/Slack notifications on publish success or failure
- [ ] Multi-tenant SaaS billing via Stripe