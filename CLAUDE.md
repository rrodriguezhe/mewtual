# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Mewtual ("Plataforma para emparejamiento responsable de gatos") is a Django monolith for responsible cat-breeding matchmaking — cat owners create profiles for their cats, swipe-match compatible cats for breeding, chat with matches, and schedule appointments. All domain code (models, templates, messages) is written in Spanish.

There is only a `backend/` Django project — no separate frontend app. Pages are server-rendered Django templates; a parallel DRF API exists on some apps but is only partially wired up (see Architecture below).

## Commands

All commands run from `backend/` (where `manage.py` lives):

```bash
cd backend
python manage.py runserver          # dev server
python manage.py migrate            # apply migrations
python manage.py makemigrations <app>
python manage.py test <app>         # run one app's tests, e.g. `python manage.py test cats`
python manage.py test               # run all tests
python manage.py createsuperuser
```

Database (Postgres, required — settings.py has no fallback/sqlite):

```bash
docker-compose up -d                # starts Postgres on host port 5433 (container 5432)
```

Dependencies:

```bash
pip install -r requirements.txt
```
Note: `requirements.txt` is UTF-16 encoded; editing it with plain-text tools may corrupt it — verify encoding after edits (`file requirements.txt`) or normalize it to UTF-8 first.

Environment: `.env` at the repo root (sibling to `backend/`, loaded via `BASE_DIR.parent / '.env'` in `config/settings.py`) must define `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.

Test files currently exist as empty Django boilerplate stubs in every app — there is no real test coverage to run or extend as a pattern.

## Architecture

Django apps under `backend/`, each following the standard `models.py` / `serializers.py` / `views.py` / `urls.py` layout, registered in `config/settings.py` `INSTALLED_APPS`:

- **users** — `Profile` (1:1 with `django.contrib.auth.User`, holds location, reputation, account status) and `Block` (user-to-user blocking). Owns session auth views: `login_view`, `register_view`, `logout_view` (`users/urls.py`, `app_name='users'`). Registration creates the `User` + `Profile` together inside a transaction.
- **cats** — `Cat` (owned by a `User`), plus `Vaccine`, `MedicalRecord`, `Favorite`. `cats/views.py` holds the core "cruce responsable" (responsible breeding) eligibility rules — `puede_cruce_responsable(gato)` requires an unexpired `Vaccine`, at least one `MedicalRecord` with an attached document, and `esterilizado=False`. Other apps (`matching`) import these helpers directly rather than duplicating the logic.
- **matching** — `Match` (gato_emisor → gato_receptor, with estado PENDIENTE/ACEPTADO/RECHAZADO). `swipe_view` (`matching/views.py`) is the matchmaking core: it picks the active cat, filters candidates by opposite sex + responsible-breeding eligibility, excludes cats already swiped in either direction, and renders one candidate at a time.
- **chat** — `Chat` (1:1 with a `Match`) and `Message`. Only unlocked once a `Match` exists.
- **appointments** — `Appointment`, tied to a `Match`, for scheduling in-person meetups (estado PENDIENTE/ACEPTADA/CANCELADA).
- **adoption** — `AdoptionPost` tied to a `Cat` (estado DISPONIBLE/ADOPTADO). Independent of the matching flow.
- **reports** — `Report`, user-to-user (usuario_reportante / usuario_reportado), for moderation.

Cross-app model dependencies flow one direction: `matching` and `adoption` import `cats.models.Cat`; `chat` and `appointments` import `matching.models.Match`. Keep new cross-app logic following that direction rather than introducing back-references.

### URL wiring (`config/urls.py`)

Each app is mounted twice in places — once under an `api/<app>/` prefix for DRF routers, and once at a bare `<app>/` prefix for template views — but **not consistently**: the top-level `api/cats/`, `api/users/`, `api/matching/`, `api/chat/` includes are commented out in `config/urls.py`. Only `cats` currently exposes its DRF router internally (mounted at `cats/api/` via `cats/urls.py`), plus `api/appointments/`, `api/adoption/`, and `api/reports/` are live at the top level. Check `config/urls.py` before assuming an app's REST API is reachable.

Root path `/` redirects to `users:login`. `LOGIN_URL`, `LOGIN_REDIRECT_URL` (`matching:home`), and `LOGOUT_REDIRECT_URL` are set in `config/settings.py`.

### Auth model

Plain Django session auth (`django.contrib.auth`), not DRF token/JWT auth — there is no `REST_FRAMEWORK` block in settings. Template views use `@login_required`; the one hardened ViewSet (`CatViewSet`) scopes its queryset to `request.user` and sets `permission_classes = [permissions.IsAuthenticated]` explicitly — other ViewSets (`MatchViewSet`, `UserViewSet`, etc.) do not, and return unfiltered querysets.

### Media

User uploads (`profiles/`, `cats/`, `vaccines/`, `medical_records/`) go to `backend/media/`, served via `MEDIA_URL`/`MEDIA_ROOT` only when `DEBUG=True`.

### Locale

`LANGUAGE_CODE = 'es'`, `TIME_ZONE = 'America/Bogota'`. Match this in any new field names, template strings, or user-facing messages.
