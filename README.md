# Friday.social interview environment (empty project)

Set up in advance as requested by the employer. The `core` app is intentionally empty.
No Event API, models, permissions, auth endpoints, schema endpoints or exercise tests exist here.

    cd /Users/samsul/Projects/Interviews/friday-social/interview-env
    source .venv/bin/activate
    brew services start postgresql@16      # if not already running
    python manage.py check
    python manage.py migrate
    pytest
    python manage.py runserver

SQLite fallback (employer-approved): `USE_SQLITE=1 python manage.py migrate` etc.

## PostgreSQL connection

Local PostgreSQL 16 (Homebrew), already configured in `config/settings.py`.

| Setting | Value |
| --- | --- |
| Host / port | `localhost` / `5432` |
| Database | `friday_interview` |
| User | `samsul` (no password) |

    pg_isready -h localhost -p 5432            # confirm it is up
    brew services start postgresql@16          # start it if not
    psql -h localhost -d friday_interview      # psql shell (\dt lists tables, \q quits)
    python manage.py dbshell                   # same, via Django (venv active)

Settings read `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` from the environment if set.
