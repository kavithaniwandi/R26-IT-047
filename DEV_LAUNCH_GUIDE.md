# 🚀 Local Development & Launching Quick-Start Guide

Welcome to the **Disaster Relief Medical Donation Module** (`R26-IT-047`).  
This document outlines the exact commands to set up the Python virtual environment (`venv`), install dependencies, run tests, and launch all backend & frontend services.

For full architectural documentation, refer to [docs/11_development_launch_guide.md](./docs/11_development_launch_guide.md).

---

## ⚡ 1. Fast Launch (Day-to-Day Development)

If you have already installed dependencies and trained the ML models:

### Terminal 1: FastAPI Backend
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.models.main:app --host 127.0.0.1 --port 8000 --reload
```
* **Swagger API Docs:** [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)
* **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### Terminal 2: React Portals (All 5 Portals)
```powershell
cd frontend
npm run dev:all
```

---

## 🛠️ 2. First-Time Setup Instructions

### Step 1: Virtual Environment Setup (`venv`)

#### Windows (PowerShell)
```powershell
# If execution policy blocks script execution:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Create & activate venv
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### Windows (Command Prompt - `cmd.exe`)
```cmd
cd backend
python -m venv venv
venv\Scripts\activate.bat
```

#### macOS / Linux / WSL / Git Bash
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

---

### Step 2: Install Dependencies

```powershell
# 1. Backend Python Dependencies (inside active venv)
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt

# 2. Frontend Node Dependencies
cd ..\frontend
npm install
```

---

### Step 3: Train Machine Learning Pipeline

```powershell
# From project root with venv active:
cd ..
python ml_pipeline.py
```
> Trains 4 Random Forest models (Flood, Landslide, Camp Suitability, Priority Scorer) and exports `.joblib` files to `backend/ml_models/`.

---

### Step 4: Run Automated Test Suite

```powershell
cd backend
python -m pytest tests/ -v
# Expected: 27 passed in ~16s
```

---

## 🌐 3. Stakeholder Portals Map & Test Logins

All portals run concurrently on independent local ports:

| Portal | Port & URL | Default Test Email | Password | Role |
| :--- | :--- | :--- | :--- | :--- |
| **Admin Command Center** | [http://localhost:5173](http://localhost:5173) | `admin@disaster.relief.lk` | `Admin@2026!` | `admin` |
| **Victim SOS Portal** | [http://localhost:5174](http://localhost:5174) | `victim@kaduwela.lk` | `Victim@2026!` | `victim` |
| **Medical Authority Console** | [http://localhost:5175](http://localhost:5175) | `authority@moh.gov.lk` | `Authority@2026!` | `authority` |
| **Relief Donor Marketplace** | [http://localhost:5176](http://localhost:5176) | `donor@redcross.lk` | `Donor@2026!` | `donor` |
| **Field Volunteer Dispatch** | [http://localhost:5177](http://localhost:5177) | `volunteer@relief.lk` | `Volunteer@2026!` | `volunteer` |

---

## 🔍 4. Useful Commands Reference

| Action | Command | Working Directory |
| :--- | :--- | :--- |
| **Run All 5 Portals** | `npm run dev:all` | `frontend/` |
| **Run Single Portal (e.g. Admin)** | `npm run dev:admin` | `frontend/` |
| **Run Single Portal (Victim)** | `npm run dev:victim` | `frontend/` |
| **Run Single Portal (Authority)** | `npm run dev:authority` | `frontend/` |
| **Run Single Portal (Donor)** | `npm run dev:donor` | `frontend/` |
| **Run Single Portal (Volunteer)** | `npm run dev:volunteer` | `frontend/` |
| **Run Pytest Suite** | `python -m pytest tests/ -v` | `backend/` |
| **Retrain ML Models** | `python ml_pipeline.py` | Root / |
| **Docker Compose Full Stack** | `docker-compose --env-file .env.docker up --build -d` | Root / |

---
