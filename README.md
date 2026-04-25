# SkillSwap Starter

A beginner-friendly Django + PostgreSQL web app starter for a Skill Swap Platform.

## Features included

- User registration, login, logout
- User profiles with bio, availability, and location
- Skill management: skills users can teach and want to learn
- Explore users with filters
- Weighted complementary match suggestions
- Skill exchange request flow: send, accept, reject, cancel
- Accepted requests automatically create exchange sessions
- Jitsi Meet video call embedded in session page
- Session notes, mini assignment, learner reflection
- Mark session completed
- Reviews and ratings after completed sessions
- Favorites system
- Proof artifacts for growth timeline
- Challenge pages and submissions
- Leaderboard
- User reporting/moderation model
- Django admin panel
- Dark mode toggle
- Render/Railway-ready Procfile, Gunicorn, Whitenoise
- Dockerfile and Docker Compose

## Local setup

1. Install Python 3.12+, Git, VS Code, and PostgreSQL.
2. Open a terminal in this folder.
3. Create a virtual environment:

```bash
python -m venv venv
```

4. Activate it:

Windows:
```bash
venv\Scripts\activate
```

Mac/Linux:
```bash
source venv/bin/activate
```

5. Install packages:

```bash
pip install -r requirements.txt
```

6. Create `.env` from `.env.example` and edit values:

```bash
copy .env.example .env
```

7. Create the database in PostgreSQL or use Docker Compose.

8. Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

9. Create admin user:

```bash
python manage.py createsuperuser
```

10. Run the server:

```bash
python manage.py runserver
```

Open: http://127.0.0.1:8000/

## Docker setup

```bash
docker compose up --build
```

Then open: http://127.0.0.1:8000/

## Deployment notes

Set these environment variables on Render or Railway:

- SECRET_KEY
- DEBUG=False
- ALLOWED_HOSTS=your-domain.onrender.com or your Railway domain
- DATABASE_URL=provided by managed PostgreSQL
- CSRF_TRUSTED_ORIGINS=https://your-domain

Build command:

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

Start command:

```bash
gunicorn config.wsgi:application
```
