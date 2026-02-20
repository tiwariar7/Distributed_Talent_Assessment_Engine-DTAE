# ⚡ Distributed Talent Assessment Engine (DTAE)

[![Kubernetes Ready](https://img.shields.io/badge/Kubernetes-Ready-blue.svg?style=flat&logo=kubernetes)](https://github.com/tiwariar7/Distributed-Talent-Assessment-Engine-DTAE-)
[![Docker Sandbox Build](https://img.shields.io/badge/Docker-Sandbox-orange.svg?style=flat&logo=docker)](https://github.com/tiwariar7/Distributed-Talent-Assessment-Engine-DTAE-)
[![Celery Distributed](https://img.shields.io/badge/Celery-Distributed-green.svg?style=flat&logo=celery)](https://github.com/tiwariar7/Distributed-Talent-Assessment-Engine-DTAE-)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A high-performance, production-ready coding assessment platform built to evaluate candidates at scale. Featuring a **hybrid relational-document storage model**, **lock-free optimistic concurrency**, **secure multi-language sandboxed execution**, and **real-time log streaming**.

---

## Quick links

- **Primary README**: `README.md` (this file)
- **Local development**: see the `frontend-next/` and `apps/` folders
- **Kubernetes / infra**: [infrastructure/kubernetes/](infrastructure/kubernetes/)

---

## Quickstart

These steps get a developer environment running quickly (requires Docker and Python 3.11+).

1. Install Python dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # or `.venv\\Scripts\\activate` on Windows
pip install -r requirements.txt
```

2. Start local services with Docker Compose (Postgres, Redis, CouchDB, RabbitMQ):

```bash
docker-compose up --build
```

3. Run migrations and seed data:

```bash
python manage.py migrate
python manage.py loaddata initial_data.json  # if present
```

4. Start the Django development server:

```bash
python manage.py runserver
```

5. (Optional) Start the Next.js frontend:

```bash
cd frontend-next
npm install
npm run dev
```

---

## Local Development

- Backend: the Django app lives under `apps/`.
- Frontend: `frontend-next/` contains the Next.js application.
- Config: environment-specific config lives in `config/` (see `settings.py` and `settings_test.py`).

Recommended workflow:

1. Create a feature branch.
2. Run unit tests and linters before pushing.
3. Open a PR with tests that demonstrate the change.

---

## Running tests

Run the test suite with:

```bash
pip install -r requirements.txt
pytest -q
```

Use `pytest -k <pattern>` to run a subset of tests.

---

## Docker & Production

- `docker-compose.yml` is for development and sandboxed runs.
- `docker-compose.prod.yml` and the `Dockerfile` provide a production-oriented build.
- Kubernetes manifests and Helm charts are under `infrastructure/kubernetes/`.

Recommended production checklist:

1. Run security scans on Docker images.
2. Ensure secrets are stored in a secret manager (do not keep in repo).
3. Configure Horizontal Pod Autoscalers for Celery workers and worker queues.

---

## Contributing

We welcome contributions. Please:

1. Fork the repository and create a feature branch.
2. Keep changes focused and add tests for new behavior.
3. Run `pytest` and ensure all tests pass locally.
4. Open a pull request with a clear description and reference to related issues.

See `CONTRIBUTING.md` if present for more details.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Contact

For questions, open an issue or contact the maintainers via the repository.

---

## Verification & Testing
To execute backend API and concurrency retry tests locally:
```bash
pip install -r requirements.txt
pytest
```



- Note: Improve responsive styles and layouts.


- Note: Update validation checks and constraints.
