# OnePulse Social Publisher

A Django CRUD application for managing and scheduling social media content.

## Requirements Met
- Django Templates for rendering
- **PostgreSQL** as the database management system
- Django's built-in session-based authentication (`authenticate`, `login`, `logout`, `@login_required`)
- Authorization: all create/update/delete routes protected — unauthenticated users redirected to `/login/`
- Multiple data entities with User model relationships
- Full CRUD across Posts, Organizations, Social Accounts, Staff, Roles
- Deployable to Heroku

## Local Setup with PostgreSQL

```bash
# 1. Create the database
createdb onepulse_db

# 2. Install dependencies
pipenv install

# 3. Set environment variables
cp .env.example .env
# Edit .env — set DATABASE_URL and a strong SECRET_KEY

# 4. Activate environment
pipenv shell

# 5. Run migrations
python manage.py migrate

# 6. Create an admin user
python manage.py createsuperuser

# 7. Start the server
python manage.py runserver
```

## Heroku Deployment

```bash
heroku create onepulse-social-publisher
heroku addons:create heroku-postgresql:essential-0
heroku config:set SECRET_KEY=your-secret-key DEBUG=False
git add . && git commit -m "Deploy"
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
heroku open
```

## Login Credentials (local dev after running migrate + seed)
- Email: `admin@vaoneagency.com` / Password: `password123`
- Email: `vaone.aj@gmail.com` / Password: `password456`

## Authentication
Uses Django's built-in `AbstractUser`, `authenticate()`, `login()`, `logout()`,
and `@login_required` decorator on all protected views.
