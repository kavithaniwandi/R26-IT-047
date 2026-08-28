# Disaster Relief Multi-Portal Frontend

**Project ID:** `R26-IT-047`  
**Component Owner:** Kavitha — *SOS Alerting, Risk Heatmap Optimization & Priority-Based Smart Matching*  
**Technology:** React 19 + Vite 8 + Leaflet + Chart.js + Lucide Icons

This package contains the single-page application (SPA) serving **five dedicated stakeholder portals** simultaneously over independent TCP ports.

---

## 🚀 Quick Launch

### 1. Install Dependencies
```powershell
npm install
```

### 2. Launch All 5 Portals Simultaneously
```powershell
npm run dev:all
```
> Spawns all five independent Vite instances using `start_portals.js` with color-coded logging and unified shutdown.

---

## 🌐 Stakeholder Portal Port Map

| Portal | Port & URL | npm Command | Default Role |
| :--- | :--- | :--- | :--- |
| **Admin Command Center** | [http://localhost:5173](http://localhost:5173) | `npm run dev:admin` | `admin` |
| **Victim SOS Portal** | [http://localhost:5174](http://localhost:5174) | `npm run dev:victim` | `victim` |
| **Medical Authority Console** | [http://localhost:5175](http://localhost:5175) | `npm run dev:authority` | `authority` |
| **Relief Donor Marketplace** | [http://localhost:5176](http://localhost:5176) | `npm run dev:donor` | `donor` |
| **Field Volunteer Dispatch** | [http://localhost:5177](http://localhost:5177) | `npm run dev:volunteer` | `volunteer` |

---

## 🔑 Default Test Credentials

| Email | Password | Role |
| :--- | :--- | :--- |
| `admin@disaster.relief.lk` | `Admin@2026!` | Admin |
| `victim@kaduwela.lk` | `Victim@2026!` | Victim |
| `authority@moh.gov.lk` | `Authority@2026!` | Authority |
| `donor@redcross.lk` | `Donor@2026!` | Donor |
| `volunteer@relief.lk` | `Volunteer@2026!` | Volunteer |

---

## 📚 Related Documentation

- [08. Frontend Portal Architecture Guide](../docs/08_frontend_portal_guide.md)
- [11. Developer Launching & Setup Guide](../docs/11_development_launch_guide.md)
- [01. System Architecture](../docs/01_system_architecture.md)
