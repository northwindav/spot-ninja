# GitHub Actions Build Guide

## Overview

The Spot-Ninja project uses GitHub Actions to build the WindNinja Docker container without requiring local Docker Desktop.

### Workflow File
[`.github/workflows/docker-build.yml`](.docker-build.yml)

---

## How to Use

### 1. Push Repository to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/spot-ninja.git
git branch -M main
git push -u origin main
```

### 2. Trigger the Build

**Option A: Manual Trigger (Recommended)**
- Go to: https://github.com/YOUR_USERNAME/spot-ninja/actions
- Select workflow: **Build WindNinja Docker Image**
- Click: **Run workflow**
- Wait: 30-45 minutes for build to complete

**Option B: Automatic Trigger**
- Build runs automatically on push to `main` branch
- Or when editing `docker/Dockerfile` or this workflow file

### 3. Download Built Image

Once build completes:

1. Go to Actions → **Build WindNinja Docker Image** → Latest run
2. Scroll to **Artifacts** section
3. Download: **windninja-docker-image** (TAR file, ~3-4 GB)
4. Also download: **build-info** (text file with instructions)

---

## Local Usage (After Download)

### Load Image into Docker

```powershell
# PowerShell (Windows)
docker load -i windninja-image.tar

# Verify
docker images | findstr windninja
# Output: windninja    latest    <IMAGE_ID>    <SIZE>
```

### Run Container

```bash
# Verify binary
docker run --rm windninja:latest windninja --help

# Run with data
docker run -v $(pwd)/data:/data windninja:latest windninja /data/config.sta

# With debugging
docker run -e CPL_DEBUG=NINJAFOAM -v $(pwd)/data:/data windninja:latest windninja /data/config.sta
```

---

## Workflow Details

### Triggers
| Event | Condition |
|-------|-----------|
| Manual | **Actions** → **Run workflow** (recommended) |
| Push | On commit to `main` branch OR edits to `docker/Dockerfile` |
| Pull Request | Optional (can add for testing) |

### Steps
1. **Checkout** — Fetch Spot-Ninja repo
2. **Clone WindNinja** — Download official WindNinja source
3. **Setup Docker Buildx** — Use GitHub's build infrastructure
4. **Build Image** — Compile using our Dockerfile (~30-45 min)
5. **Upload Artifact** — Save TAR file for download (30-day retention)
6. **Optional: Push Registry** — Upload to GitHub Container Registry (if configured)

### Build Environment
- **OS**: Ubuntu Latest (GitHub-hosted runner)
- **Build Cache**: GitHub Actions cache (speeds up rebuilds)
- **Retention**: 30 days

---

## Advanced: Container Registry (Optional)

To push directly to GitHub Container Registry instead of downloading TAR:

### Setup (One-time)
1. Go to repo → **Settings** → **Secrets and variables** → **Actions**
2. Create secret: `REGISTRY_TOKEN` (GitHub Personal Access Token with `write:packages`)
3. Update workflow: Uncomment registry sections

### Usage After Setup
```bash
# Pull directly from registry (no download needed)
docker pull ghcr.io/YOUR_USERNAME/windninja:latest
```

---

## Troubleshooting

### Build Fails
- Check **Actions** → **Build WindNinja Docker Image** → Latest run → **Logs**
- Common issues:
  - Network timeout: Retry build
  - WindNinja repo offline: Check https://github.com/firelab/windninja
  - Disk space: GitHub provides 14 GB; large builds are OK

### Artifact Download Fails
- Check artifact retention (default: 30 days)
- Ensure GitHub account has repo access
- Try downloading from: https://github.com/YOUR_USERNAME/spot-ninja/actions

### Image Load Fails
- Verify TAR file size (~3-4 GB)
- Check disk space: `docker system df`
- Ensure Docker Desktop is running before `docker load`

---

## Alternative: Local Build (if virtualization enabled later)

Once Docker Desktop is available:

```bash
cd docker
.\build_docker.bat --tag windninja:latest
```

---

## Next Steps

1. **Immediate**: Commit and push repo to GitHub
2. **Then**: Trigger manual build from Actions page
3. **After build**: Download TAR artifact
4. **Load locally**: `docker load -i windninja-image.tar`
5. **Verify**: `docker run --rm windninja:latest windninja --help`

---

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Action](https://github.com/docker/build-push-action)
- [Artifacts Upload/Download](https://github.com/actions/upload-artifact)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
