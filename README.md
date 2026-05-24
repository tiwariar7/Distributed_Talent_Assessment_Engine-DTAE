<h1 align="center"> <b></b>Distributed Talent Assessment Engine (DTAE)</b></h1>
<p align="center">
  Scalable • Secure • Distributed • Real-Time Coding Assessment Platform
</p>

<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=00C2FF&center=true&vCenter=true&width=800&lines=Distributed+Coding+Assessment+Platform;Docker+Sandboxed+Execution;Real-Time+Code+Evaluation;Kubernetes+Ready+Architecture;Built+with+Django+%2B+Celery+%2B+Next.js" />
</p>

<div align="center">

![Stars](https://img.shields.io/github/stars/tiwariar7/Distributed-Talent-Assessment-Engine-DTAE-?style=for-the-badge&logo=github)
![Forks](https://img.shields.io/github/forks/tiwariar7/Distributed-Talent-Assessment-Engine-DTAE-?style=for-the-badge&logo=github)
![Issues](https://img.shields.io/github/issues/tiwariar7/Distributed-Talent-Assessment-Engine-DTAE-?style=for-the-badge&logo=github)
![Last Commit](https://img.shields.io/github/last-commit/tiwariar7/Distributed-Talent-Assessment-Engine-DTAE-?style=for-the-badge&logo=git)

<br>
<div align="center">

[![Kubernetes Ready](https://img.shields.io/badge/Kubernetes-Ready-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)](https://github.com/tiwariar7/Distributed-Talent-Assessment-Engine-DTAE-) 
[![Docker Sandbox](https://img.shields.io/badge/Docker-Sandbox-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://github.com/tiwariar7/Distributed-Talent-Assessment-Engine-DTAE-) 
[![Celery Distributed](https://img.shields.io/badge/Celery-Distributed-37814A?style=for-the-badge&logo=celery&logoColor=white)](https://github.com/tiwariar7/Distributed-Talent-Assessment-Engine-DTAE-) 
[![License MIT](https://img.shields.io/github/license/tiwariar7/Distributed-Talent-Assessment-Engine-DTAE-?style=for-the-badge)](https://opensource.org/licenses/MIT)

</div>

<br>

<img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=24&pause=1000&color=00C2FF&center=true&vCenter=true&width=900&lines=Distributed+Talent+Assessment+Engine;Scalable+Coding+Assessment+Platform;Docker+Sandboxed+Execution;Real-Time+Code+Evaluation;Kubernetes+Ready+Architecture" />

</div>

A high-performance, production-ready coding assessment platform built to evaluate candidates at scale. Features a hybrid relational-document storage model, lock-free optimistic concurrency, secure multi-language sandboxed execution, and real-time log streaming.

---
## Tech Stack

<p align="center">
  <img src="https://skillicons.dev/icons?i=python,django,postgres,redis,rabbitmq,docker,kubernetes,nextjs,typescript,tailwind,git,linux" />
</p>

##  Table of Contents

<div align="center">

| Section | Description |
|---------|-------------|
|  [Overview](#overview) | Project introduction & goals |
|  [Architecture](#architecture) | System design & workflow |
|  [Quick Start](#quick-start) | Setup & installation guide |
|  [Contributing](#contributing) | Contribution guidelines |
|  [License](#license) | License information |

</div>

---

## Overview

DTAE addresses the challenges of large-scale technical assessments by providing:

| Feature | Description |
|---------|-------------|
| Scalable Architecture | Distributed task processing with Celery and multiple queue workers |
| Multi-Language Support | Code execution in Python, JavaScript, Java, C++, and Go |
| Secure Execution | Isolated Docker-based sandbox for each code submission |
| Real-Time Streaming | Live log delivery during code execution |
| Concurrent Submissions | Optimistic concurrency control with automatic retry logic |
| Hybrid Storage | PostgreSQL for relational data + CouchDB for flexible submission storage |

---
##  System Architecture



```
┌─────────────┐      ┌─────────────┐      ┌─────────────────┐
│   Next.js   │────▶│   Django     │────▶│    PostgreSQL   │
│   Frontend  │◀────│   Backend    │◀────│      + CouchDB  │
└─────────────┘      └─────────────┘      └─────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   RabbitMQ  │
                    │   / Redis   │
                    └─────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │    Celery Workers      │
              │  ┌──────────────────┐  │
              │  │ Docker Sandbox   │  │
              │  │ (Code Execution) │  │
              │  └──────────────────┘  │
              └────────────────────────┘
```
---
### Technology Stack

- **Backend**: Django 4.2, Django REST Framework
- **Task Queue**: Celery with RabbitMQ broker
- **Databases**: PostgreSQL (primary), CouchDB (document store)
- **Cache**: Redis
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Orchestration**: Kubernetes, Docker
- **Monitoring**: Prometheus, Grafana (optional)

---

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend development)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/tiwariar7/Distributed-Talent-Assessment-Engine-DTAE-.git
cd Distributed-Talent-Assessment-Engine-DTAE-
```

2. Set up Python virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start infrastructure services:

```bash
docker-compose up -d
```

5. Run database migrations:

```bash
python manage.py migrate
```

6. Start the Django development server:

```bash
python manage.py runserver
```

7. (Optional) Start Celery worker:

```bash
celery -A config worker --loglevel=info
```

8. (Optional) Start Next.js frontend:

```bash
cd frontend-next
npm install
npm run dev
```

The application will be available at:
- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:3000`

---


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---


