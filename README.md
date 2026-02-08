# P&A System - Podman Infrastructure

## 🚀 Quick Start

### Install Podman (Windows)

```powershell
# As Administrator
winget install RedHat.Podman

# As regular user (new terminal)
podman machine init
podman machine start
pip install podman-compose
```

### Start the Stack

```powershell
cd C:\Users\Gustavo\.gemini\antigravity\scratch

# Start services
podman-compose -f podman-compose.yml up -d

# Wait ~15 seconds

# View Temporal UI
# Open http://localhost:8080
```

## 📋 Services

- **MySQL**: localhost:3306 (user: pna_user, pass: pna_pass)
- **Temporal Server**: localhost:7233
- **Temporal UI**: http://localhost:8080
- **Worker**: Running in container

## 🧪 Run Tests

```powershell
# All tests
podman-compose -f podman-compose.yml exec worker pytest -v tests/

# Unit only
podman-compose -f podman-compose.yml exec worker pytest -v tests/unit/

# Integration
podman-compose -f podman-compose.yml exec worker pytest -v tests/integration/

# E2E
podman-compose -f podman-compose.yml exec worker pytest -v -m e2e tests/e2e/
```

## 🛑 Stop Services

```powershell
podman-compose -f podman-compose.yml down
```

## 📖 Documentation

- **PODMAN_SETUP.md** - Complete installation and usage guide
- **testing_infrastructure.md** - Testing strategy documentation
- **.env** - Configuration (change for cloud deployment)

## ☁️ Cloud Ready

Same stack works on Linux VMs without changes:

```bash
# On Linux VM
podman-compose -f podman-compose.yml up -d
```

Update `.env` for production values!

## 🔧 Key Files

- `Containerfile` - OCI-compliant worker image
- `podman-compose.yml` - Service orchestration
- `.env` - Environment configuration
- `db/migrations/` - Database schema
- `db/seeds/` - Test data
- `backend/` - Python worker code
- `tests/` - Unit/integration/E2E tests
