# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Mewtual ("Plataforma para emparejamiento responsable de gatos") is a Django monolith for responsible cat-breeding matchmaking — cat owners create profiles for their cats, swipe-match compatible cats for breeding, chat with matches, and schedule appointments. All domain code (models, templates, messages) is written in Spanish.

There is only a `Final-Project/backend/` Django project — no separate frontend app. Pages are server-rendered Django templates; a parallel DRF API exists on some apps but is only partially wired up (see Architecture below). The Django project used to live at the repo root (`backend/`) but was relocated under `Final-Project/backend/` to keep source and deliverables together, per the course's Software Engineering II final project brief. Diagrams (UML, ER, BPMN, architecture) live in `Final-Project/Diagrams/`; written deliverables (analysis, design, proposal) live in `Deliveries/` at the repo root.

## Commands

All commands run from `Final-Project/backend/` (where `manage.py` lives):

```bash
cd Final-Project/backend
python manage.py runserver          # dev server
python manage.py migrate            # apply migrations
python manage.py makemigrations <app>
python manage.py test <app>         # run one app's tests, e.g. `python manage.py test cats`
python manage.py test               # run all tests
python manage.py createsuperuser
python manage.py seed_demo_data     # seeds demo users/cats/a match+chat+appointment for local testing
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

Environment: `.env` at `Final-Project/` (sibling to `Final-Project/backend/`, loaded via `BASE_DIR.parent / '.env'` in `config/settings.py`) must define `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.

Test files are empty Django boilerplate stubs in `chat` and `appointments` — `cats`, `matching`, `users`, `adoption`, and `reports` each have a real test suite (`TestCase`/`APITestCase`) covering business logic, form validation, ownership, and permissions (99 tests total; see Architecture below).

## Architecture

Django apps under `Final-Project/backend/`, each following the standard `models.py` / `serializers.py` / `views.py` / `urls.py` layout, registered in `config/settings.py` `INSTALLED_APPS`:

- **users** — `Profile` (1:1 with `django.contrib.auth.User`, holds location, reputation, account status) and `Block` (user-to-user blocking). Owns session auth views: `login_view`, `register_view`, `logout_view` (`users/urls.py`, `app_name='users'`). Registration creates the `User` + `Profile` together inside a transaction.
- **cats** — `Cat` (owned by a `User`), plus `Vaccine`, `MedicalRecord`, `Favorite`. `cats/views.py` holds the core "cruce responsable" (responsible breeding) eligibility rules — `puede_cruce_responsable(gato)` requires an unexpired `Vaccine`, at least one `MedicalRecord` with an attached document, and `esterilizado=False`. Other apps (`matching`) import these helpers directly rather than duplicating the logic.
- **matching** — `Match` (gato_emisor → gato_receptor, with estado PENDIENTE/ACEPTADO/RECHAZADO). `swipe_view` (`matching/views.py`) is the matchmaking core: it picks the active cat, filters candidates by opposite sex + responsible-breeding eligibility, excludes cats already swiped in either direction, and renders one candidate at a time.
- **chat** — `Chat` (1:1 with a `Match`) and `Message`. Only unlocked once a `Match` exists.
- **appointments** — `Appointment`, tied to a `Match`, for scheduling in-person meetups (estado PENDIENTE/ACEPTADA/CANCELADA).
- **adoption** — `AdoptionPost` tied to a `Cat` (estado DISPONIBLE/RESERVADA/ADOPTADA). Independent of the matching flow. Reads are open to any authenticated user; writes are restricted to the posting cat's owner (or staff) via the `IsGatoOwnerOrStaff` object permission in `adoption/views.py`. Has a template UI (`adoption/template_urls.py`, mounted at bare `adoption/`) to browse open listings, publish/edit/delete your own — separate from the DRF router in `adoption/urls.py`, which stays mounted at `api/adoption/`.
- **reports** — `Report`, user-to-user (usuario_reportante / usuario_reportado), for moderation. Non-staff users only see reports they filed (`ReportViewSet.get_queryset`); only staff can change a report's `estado` or delete it. Has a template UI (`reports/template_urls.py`, mounted at bare `reports/`) that is deliberately contextual rather than a standalone tab — `reports:crear_reporte` always requires a `?usuario=<id>` target and is only linked from a specific cat/post (e.g. a "Reportar" action on a swipe candidate or an adoption listing), not a free user picker.

Cross-app model dependencies flow one direction: `matching` and `adoption` import `cats.models.Cat`; `chat` and `appointments` import `matching.models.Match`. Keep new cross-app logic following that direction rather than introducing back-references.

### URL wiring (`config/urls.py`)

Each app is mounted twice in places — once under an `api/<app>/` prefix for DRF routers, and once at a bare `<app>/` prefix for template views — but **not consistently**: the top-level `api/cats/`, `api/users/`, `api/matching/`, `api/chat/` includes are commented out in `config/urls.py`. Instead, `cats`, `matching`, `chat`, and `users` each nest their own DRF router inside their own `urls.py`, included once at the bare `<app>/` prefix — e.g. `MatchViewSet` is reachable at `/matching/matches/`, not `/api/matching/matches/`. `appointments`, `adoption`, and `reports` are the ones actually live under `api/<app>/` at the top level; `adoption` and `reports` are *also* mounted a second time at their bare `<app>/` prefix, but that second mount points at a separate `template_urls.py` (template views only, no router) rather than double-registering the router. Check `config/urls.py` before assuming an app's REST API is reachable — and don't assume a ViewSet is safe just because it isn't under `api/`.

Root path `/` redirects to `users:login`. `LOGIN_URL`, `LOGIN_REDIRECT_URL` (`matching:swipe`), and `LOGOUT_REDIRECT_URL` are set in `config/settings.py`. There is no "Inicio"/home tab — `matching:home` (a dashboard view) still exists and works but isn't linked from any nav bar or redirect; `matching:swipe` is the de facto landing page after login.

### Auth model

Plain Django session auth (`django.contrib.auth`), not DRF token/JWT auth — there is no `REST_FRAMEWORK` block in settings. Note this means DRF's default `SessionAuthentication` "succeeds" as `AnonymousUser` for unauthenticated requests, so an `IsAuthenticated` denial comes back as 403, not 401 — see the tests in `reports/tests.py` for the concrete case. Template views use `@login_required`. Every ViewSet across every app now requires `IsAuthenticated` and scopes its queryset to data the requesting user owns or participates in (`CatViewSet`, `AdoptionPostViewSet`, `ReportViewSet`, `MatchViewSet`, `ChatViewSet`, `MessageViewSet`, `ProfileViewSet`, `BlockViewSet`, `AppointmentViewSet`); `UserViewSet` is read-only. This was previously a real gap — `MatchViewSet`/`UserViewSet`/`ChatViewSet`/`MessageViewSet`/`AppointmentViewSet` had no `permission_classes` at all and were confirmed exploitable by anonymous requests before being locked down. One non-obvious consequence of queryset-scoping instead of (or in addition to) an object-level permission: a non-participant hitting another user's match/chat/profile/block detail URL gets **404**, not 403 — the object simply isn't in their queryset, so DRF's `get_object()` never gets far enough to check object permissions (see the "non_owner"/"non_participant" tests in `matching/tests.py` and `users/tests.py` for the concrete cases).

### Media

User uploads (`profiles/`, `cats/`, `vaccines/`, `medical_records/`) go to `Final-Project/backend/media/`, served via `MEDIA_URL`/`MEDIA_ROOT` only when `DEBUG=True`.

### Locale

`LANGUAGE_CODE = 'es'`, `TIME_ZONE = 'America/Bogota'`. Match this in any new field names, template strings, or user-facing messages.
