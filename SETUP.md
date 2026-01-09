# Sonarr/Radarr Genre Tagger Setup

## Quick Start

1. **Copy environment file:**
   ```powershell
   Copy-Item .env.example .env
   ```

2. **Edit `.env` with your credentials:**
   ```
   SONARR_URL=http://your-sonarr:8989/api
   SONARR_API=your-actual-api-key
   RADARR_URL=http://your-radarr:7878/api
   RADARR_API=your-actual-api-key
   ```

3. **Run with Docker Compose:**
   ```powershell
   docker-compose up
   ```

   Or manually:
   ```powershell
   docker build -t sonarrgenretagger:latest .
   docker run --rm --env-file .env -v C:\config:/config sonarrgenretagger:latest
   ```

## Scheduling (Windows Task Scheduler)

Create a PowerShell script `run-tagger.ps1`:
```powershell
Set-Location "C:\Users\emmar\OneDrive\Projects\Sonarr\sonarr-genre-tagger"
docker-compose up
```

Schedule in Task Scheduler to run at desired intervals (daily, hourly, etc).

## Future: Vault Integration

When your homelab grows, you can integrate HashiCorp Vault for centralized secret management. See `VAULT.md` for details.

## Security Notes

- ⚠️ **NEVER** commit `.env` to git
- The `.gitignore` file prevents accidental commits
- Store `.env` in a secure location with restricted file permissions
- Consider using encrypted volumes for production
