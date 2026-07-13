# Final-Project

Course deliverable folder for Mewtual, per the Software Engineering II final project brief
(`docs/enunciado.pdf`). The application's source code is **not** duplicated here — it lives at
the repository root under [`backend/`](../backend), and stays there so there is a single copy
to keep in sync. This folder holds the documentation, diagrams, and other deliverables the
brief asks for.

## Structure

```
Final-Project/
├── docs/
│   ├── enunciado.pdf   # assignment brief (reference only, not a deliverable)
│   ├── analisis.pdf    # requirements analysis: actors, entities, business rules,
│   │                   # functional/non-functional requirements, user stories, MVP scope
│   ├── design.pdf       # design: CRC cards, UML class diagram, ER diagram,
│   │                   # BPMN (matching flow), architecture diagram, UI mockups
│   ├── final-report.pdf # (pending) consolidated report required by the brief:
│   │                   # architecture, design patterns, API docs, DB schema,
│   │                   # testing strategy, setup/deployment, and evaluation
│   └── diagrams/        # full-resolution diagram exports (UML, ER, BPMN, architecture)
├── evidence/            # per-user-story screenshots/clips proving implemented HUs work
└── demo/                # slides and/or a link to the mandatory 15-minute demo recording
```

`final-report.pdf` is not written yet — it needs to compile the sections above plus:
API endpoint documentation, the two required design patterns (with rationale), the testing
strategy, and a critical evaluation (strengths/limitations/future work), per the brief's
"Methodology and Deliverables" section.

## Setup and usage

The application itself is the Django project under `backend/`. See the repository root
[`CLAUDE.md`](../CLAUDE.md) for architecture notes, or run it directly:

```bash
docker-compose up -d        # Postgres, from the repo root
cd backend
pip install -r ../requirements.txt
python manage.py migrate
python manage.py runserver
```

Requires a `.env` file at the repository root with `DB_NAME`, `DB_USER`, `DB_PASSWORD`,
`DB_HOST`, `DB_PORT` — see `config/settings.py` for how it's loaded.
