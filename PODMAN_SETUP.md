# WSL2 + Podman Setup Guide (Windows)

## ⚠️ Current Issue

You need to install **WSL2** (Windows Subsystem for Linux) first. Podman requires it on Windows.

---

## 🔧 Installation Steps

### Step 1: Install WSL2 (Requires Administrator)

**Option A - Using the Script:**

1. Right-click on **PowerShell**
2. Select **"Run as Administrator"**
3. Navigate to the project:
   ```powershell
   cd C:\Users\Gustavo\.gemini\antigravity\scratch
   ```
4. Run the installation script:
   ```powershell
   .\install-wsl2.ps1
   ```

**Option B - Manual Installation:**

1. Right-click on **PowerShell**
2. Select **"Run as Administrator"**
3. Run:
   ```powershell
   wsl --install
   ```

### Step 2: Restart Your Computer

**You MUST restart Windows after WSL installation!**

### Step 3: Complete Ubuntu Setup (After Restart)

After reboot, Ubuntu will install automatically:
1. Wait for Ubuntu installation to complete
2. Create a **username** (e.g., "gustavo")
3. Create a **password** (you'll need this later)
4. Close the Ubuntu window when done

### Step 4: Initialize Podman Machine

Open a **regular** PowerShell (not as admin):

```powershell
cd C:\Users\Gustavo\.gemini\antigravity\scratch

# Initialize Podman machine
podman machine init

# Start Podman machine
podman machine start

# Verify installation
podman --version
```

### Step 5: Install podman-compose

```powershell
pip install podman-compose
```

### Step 6: Start the P&A Stack!

```powershell
podman-compose -f podman-compose.yml up -d
```

Wait ~15 seconds, then open: http://localhost:8080

---

## 📋 Quick Reference

### After all installation is complete:

```powershell
# Start stack
podman-compose -f podman-compose.yml up -d

# Stop stack
podman-compose -f podman-compose.yml down

# View logs
podman-compose -f podman-compose.yml logs -f

# Check status
podman-compose -f podman-compose.yml ps
```

---

## 🐛 Troubleshooting

### "WSL installation incomplete"
- Make sure you restarted Windows after `wsl --install`
- Check WSL status: `wsl --list --verbose`

### "podman machine not found"
- Run: `podman machine init`
- Then: `podman machine start`

### "Permission denied"
- Don't run Podman commands as Administrator (except WSL install)
- Use regular PowerShell for Podman

---

## ✅ What You Need to Do Now

1. **Run PowerShell as Administrator**
2. **Execute**: `wsl --install`
3. **Restart your computer**
4. **Come back here** after restart and continue with Step 4

Let me know when you've restarted and I'll help you finish the setup! 🚀
