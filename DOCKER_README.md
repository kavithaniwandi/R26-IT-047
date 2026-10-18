# 🐳 Disaster Relief API — Dockerized MySQL Setup

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network: relief_net             │
│                                                           │
│  ┌──────────────┐    ┌─────────────────┐    ┌─────────┐ │
│  │   MySQL 8.0  │◄───│  FastAPI Backend │    │Adminer  │ │
│  │  Port: 3306  │    │   Port: 8000    │    │Port:8080│ │
│  │disaster_     │    │  SQLAlchemy +   │    │DB GUI   │ │
│  │relief DB     │    │  PyMySQL driver │    │         │ │
│  └──────────────┘    └─────────────────┘    └─────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Docker Desktop (running)
- Docker Compose v2+

### 1. Start the Stack
```powershell
# Option A: Using the helper script
.\docker-start.ps1 up

# Option B: Direct docker-compose
docker-compose --env-file .env.docker up --build -d
```

### 2. Verify Services
| Service       | URL                              | Purpose              |
|---------------|----------------------------------|----------------------|
| API           | http://localhost:8000            | FastAPI backend      |
| Swagger UI    | http://localhost:8000/api/docs   | Interactive API docs |
| ReDoc         | http://localhost:8000/api/redoc  | API documentation    |
| Health Check  | http://localhost:8000/health     | Liveness probe       |
| Adminer       | http://localhost:8080            | MySQL web GUI        |

### 3. Check Container Status
```powershell
docker-compose ps
docker-compose logs -f backend   # Follow backend logs
docker-compose logs -f db        # Follow MySQL logs
```

## Default Credentials

### API Users (seeded on first start)
| Role      | Email                        | Password           |
|-----------|------------------------------|--------------------|
| Admin     | admin@disaster.relief.lk     | Admin@2026!        |
| Authority | authority@moh.gov.lk         | Authority@2026!    |
| Donor     | donor@redcross.lk            | Donor@2026!        |
| Victim    | victim@kaduwela.lk           | Victim@2026!       |

### MySQL Database
| Parameter | Value             |
|-----------|-------------------|
| Host      | localhost:3306    |
| Database  | disaster_relief   |
| User      | relief_user       |
| Password  | relief_pass       |
| Root Pass | rootpassword      |

### Adminer Login (http://localhost:8080)
- **System:** MySQL
- **Server:** db
- **Username:** relief_user
- **Password:** relief_pass
- **Database:** disaster_relief

## Postman Testing

1. Open Postman
2. Import Collection: `docs/postman/Disaster_Relief_API.postman_collection.json`
3. Import Environment: `docs/postman/Disaster_Relief_LocalDocker.postman_environment.json`
4. Select environment: **Disaster Relief — Local Docker**
5. Run `Auth > POST /auth/login — Admin` (token auto-saved)
6. Test any endpoint!

## API Endpoints Summary

### Authentication
- `POST /api/v1/auth/register` — Register new user
- `POST /api/v1/auth/login` — Login (returns JWT)
- `GET  /api/v1/auth/me` — Current user profile

### SOS Alerts
- `POST /api/v1/sos` — Submit SOS alert
- `GET  /api/v1/sos` — List all SOS alerts
- `GET  /api/v1/sos/{id}` — Get specific SOS
- `PATCH /api/v1/sos/{id}/status` — Update SOS status

### Medical Camps
- `POST /api/v1/camps` — Create camp
- `GET  /api/v1/camps` — List camps
- `PATCH /api/v1/camps/{id}/status` — Approve/update

### Donations
- `GET  /api/v1/donations` — List donation needs
- `POST /api/v1/donations` — Make donation pledge
- `GET  /api/v1/donations/smart-match` — AI-powered matching

### Victims
- `POST /api/v1/victims` — Register victim
- `GET  /api/v1/victims` — List victims
- `GET  /api/v1/victims/{id}` — Get victim details

### Others
- `GET  /api/v1/heatmap` — Risk heatmap data
- `POST /api/v1/sms/inbound` — Simulate SMS SOS
- `GET  /api/v1/admin/stats` — Dashboard statistics
- `GET  /api/v1/notifications` — User notifications

## Helper Commands

```powershell
.\docker-start.ps1 up        # Start all services
.\docker-start.ps1 down      # Stop all services
.\docker-start.ps1 logs      # Follow backend logs
.\docker-start.ps1 ps        # Check container status
.\docker-start.ps1 shell     # Open backend shell
.\docker-start.ps1 db-shell  # Open MySQL shell
.\docker-start.ps1 clean     # Remove containers + volumes
.\docker-start.ps1 rebuild   # Force rebuild images
```

## Database Schema

MySQL tables auto-created by SQLAlchemy on startup:
- `roles` — Role definitions (admin, victim, donor, authority, volunteer)
- `users` — User accounts with RBAC
- `sos_requests` — SOS alert submissions
- `medical_camps` — Camp proposals and approvals
- `donation_items` — Items needed per SOS
- `donations` — Donor pledges
- `notifications` — System notifications
- `victims` — Victim registration records
- `sms_message_logs` — SMS gateway audit trail
- `risk_predictions` — ML heatmap predictions

## File Structure

```
SDM Project refine/
├── docker-compose.yml          # 🐳 Main orchestration
├── .env.docker                 # 🔑 Docker env variables
├── docker-start.ps1            # ⚡ Helper script
├── DOCKER_README.md            # 📖 This file
├── docker/
│   └── mysql/
│       └── init/
│           └── 01_init.sql     # 🗄️ MySQL initialization
├── backend/
│   ├── Dockerfile              # 🐳 Backend container
│   ├── .dockerignore           # 🚫 Build exclusions
│   ├── requirements.txt        # 📦 Python deps (+ MySQL)
│   └── app/
│       ├── database.py         # ✅ MySQL/SQLite dual support
│       └── ...
└── docs/
    └── postman/
        ├── Disaster_Relief_API.postman_collection.json
        └── Disaster_Relief_LocalDocker.postman_environment.json
```
