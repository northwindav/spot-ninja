# Next Steps: GitHub Build & Phase 3 Prep

## Immediate (GitHub Setup)

### 1. Initialize Git Repository (if not already done)
```bash
cd spot-ninja
git init
git add .
git commit -m "Phase 1-2: Project scaffolding + GitHub Actions build setup"
```

### 2. Create GitHub Repository
- Go to https://github.com/new
- Create repository: `spot-ninja`
- Choose: Private or Public (public = free container registry access)

### 3. Push to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/spot-ninja.git
git branch -M main
git push -u origin main
```

### 4. Trigger Build
- Go to: https://github.com/YOUR_USERNAME/spot-ninja/actions
- Click: **Build WindNinja Docker Image** workflow
- Click: **Run workflow**
- Status: Will show pending → building → completed (30-45 min)

### 5. Download Artifact
Once complete:
- Go to latest run → **Artifacts** section
- Download: `windninja-docker-image` (TAR, ~3-4 GB)
- Save to: `spot-ninja/` directory

### 6. Load Image Locally
```powershell
cd spot-ninja
docker load -i windninja-image.tar

# Verify
docker images | findstr windninja
```

---

## While Build is Running: Phase 3 Prep

**Opportunity**: Start Phase 3 (DEM & Weather Retrieval) while GitHub builds the container.

### Phase 3 Deliverables
- `scripts/dem_retriever.py` — Download DEMs from CanElevation AWS S3
- `scripts/weather_retriever.py` — Fetch HRDPS/GDPS from MSC GeoMet
- `scripts/validators.py` — Input validation (lat/lon, domain bounds, etc.)
- `scripts/requirements.txt` — Python dependencies (boto3, requests, pyyaml, GDAL)
- Testing framework for both retrievers

### Phase 3 Estimated Time
- DEM retriever: 2-3 hours
- Weather retriever: 2-3 hours  
- Validators & testing: 1-2 hours
- **Total**: 5-8 hours

---

## Recommended Workflow

| Time | Activity |
|------|----------|
| **Now** | Commit repo + trigger GitHub build |
| **Next 5 min** | Start Phase 3 DEM retriever development |
| **30-45 min later** | GitHub build completes; download artifact |
| **Next session** | Load container + test Phase 3 modules |
| **Final** | Integrate DEM/weather retrievers with container |

---

## Resources

- **GitHub Actions Setup**: See [GITHUB_ACTIONS.md](./GITHUB_ACTIONS.md)
- **Phase 3 Planning**: See [README.md](./README.md) (Specific steps section)
- **CanElevation Docs**: https://registry.opendata.aws/canelevation-dem/
- **MSC GeoMet**: https://api.weather.gc.ca/

---

## Summary

✅ **Phase 2 (Container Build)**: READY
- Dockerfile configured
- GitHub Actions workflow ready
- No local Docker needed

⏭️ **Next**: Push to GitHub + trigger build while starting Phase 3 data retrieval

❓ **Questions?** See [GITHUB_ACTIONS.md](./GITHUB_ACTIONS.md) or [SETUP.md](./SETUP.md)
