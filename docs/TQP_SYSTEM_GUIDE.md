# The Quiet Pilgrim Expense System - Operations Guide

## System Overview

**Status:** ✅ OPERATIONAL
**VPS:** 77.42.37.42
**Deployed:** 2026-03-14
**User:** helm

## Live Endpoints

- **Health Check:** http://77.42.37.42/api/health
- **API Documentation:** http://77.42.37.42/docs
- **OpenAPI Spec:** http://77.42.37.42/openapi.json
- **VPS Monitor:** http://77.42.37.42/vps-monitor.html

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx (Port 80)                      │
│                 Reverse Proxy & Routing                 │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              FastAPI Application                        │
│              (expense-api.service)                      │
│              Port 8000, 2 Workers                       │
├─────────────────────────────────────────────────────────┤
│  Services:                                              │
│  • OCR Service (Google Vision + OpenAI)                 │
│  • AI Extraction (GPT-4)                                │
│  • Google Sheets Integration                            │
│  • Google Drive Integration                             │
│  • Notification Service                                 │
│  • Confidence Scoring                                   │
└─────────────────────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
┌────────▼────────┐   ┌─────────▼──────────┐
│   Redis Server  │   │  Google Cloud APIs │
│   (Port 6379)   │   │  • Sheets          │
│   Background    │   │  • Drive           │
│   Tasks         │   │  • Vision          │
└─────────────────┘   └────────────────────┘
```

## Services Running

1. **expense-api.service** - Main application (systemd)
2. **nginx** - Web server and reverse proxy
3. **redis-server** - Background task queue

## Configuration Files

### System Config
- **Service:** `/etc/systemd/system/expense-api.service`
- **Nginx:** `/etc/nginx/sites-available/expense-system`
- **Application:** `/var/www/expense-system/backend/`

### Application Files
- **Main:** `/var/www/expense-system/backend/main.py`
- **Config:** `/var/www/expense-system/backend/config.py`
- **Environment:** `/var/www/expense-system/backend/.env`
- **Credentials:** `/var/www/expense-system/credentials/google-credentials.json`

## Management Commands

### Using VPS Manager (Recommended)
```bash
# From Windows machine
cd C:\Users\ASUS
python vps_manager.py status      # Check service status
python vps_manager.py health      # Health check
python vps_manager.py monitor     # Full system report
python vps_manager.py logs        # View logs
python vps_manager.py restart     # Restart service
python vps_manager.py test        # Test endpoints
```

### Direct SSH Commands
```bash
# Service management
ssh helm@77.42.37.42 'sudo systemctl status expense-api'
ssh helm@77.42.37.42 'sudo systemctl restart expense-api'
ssh helm@77.42.37.42 'sudo systemctl stop expense-api'
ssh helm@77.42.37.42 'sudo systemctl start expense-api'

# View logs
ssh helm@77.42.37.42 'sudo journalctl -u expense-api -f'
ssh helm@77.42.37.42 'sudo journalctl -u expense-api -n 100'

# Check health
ssh helm@77.42.37.42 'curl http://localhost:8000/api/health'
```

## Google Services Integration

### Connected Services
- **Google Sheets:** Connected ✅
  - Personal: 150p817Bh1BgsWfks_lzdYpLZZzJI-2w_Aqd1j2LFKvk
  - Business: 1rdF88WroRv8MLgSiS6cymbj-lGl35FcbXSEMgDhjHhQ
  - Moonspoon: 1u-bP2y-_bkIuaTg4awciiAMWvB3P19Yy-cisT20zZUc

- **Google Drive:** Connected ✅
  - Personal: 1kc9MyhGWib1lPwSUpM-bjim5B2OMbBNN
  - Business: 1REs1OyoArCUNXVksGGiir4DYX2phAmLB
  - Moonspoon: 1ZTK7rD5XWd9Tou1V9f61rL9GKuQjLla8

- **Google Vision:** Connected ✅ (Primary OCR)

### Service Account
- **Project:** the-quiet-pilgrim
- **Credentials:** /var/www/expense-system/credentials/google-credentials.json

## API Configuration

### OpenAI Integration
- **Model:** gpt-4-turbo-preview
- **Temperature:** 0.1 (for consistent extraction)
- **Max Tokens:** 2000

### OCR Configuration
- **Primary:** Google Vision
- **Fallback:** OpenAI Vision
- **Auto-Approve Threshold:** 85%

## Deployment & Updates

### Deploy Code Updates
```python
# Using VPS Manager
manager = VPSManager()
manager.connect()
manager.deploy_update('C:\\path\\to\\local\\file.py', '/var/www/expense-system/backend/file.py')
```

### Manual Deployment
```bash
# Upload file via SCP
scp local_file.py helm@77.42.37.42:/var/www/expense-system/backend/

# Restart service
ssh helm@77.42.37.42 'sudo systemctl restart expense-api'
```

## Monitoring & Health Checks

### Health Endpoint Response
```json
{
  "status": "healthy",
  "services": {
    "google_sheets": "connected",
    "google_drive": "connected",
    "ocr_provider": "google_vision",
    "telegram_notifications": "disabled"
  },
  "entities": {
    "personal": {...},
    "business": {...},
    "moonspoon": {...}
  },
  "timestamp": "2026-03-14T04:07:04.680534"
}
```

### System Resources
- **Memory:** 15GB total, ~5GB used
- **Disk:** 75GB total, 15GB used (21%)
- **CPU:** Low usage with 2 workers

## Troubleshooting

### Service Not Starting
```bash
# Check logs for errors
sudo journalctl -u expense-api -n 50

# Check configuration
cd /var/www/expense-system/backend
source venv/bin/activate
python -c "from config import settings; print('Config OK')"
```

### Google API Errors
```bash
# Verify credentials exist
ls -la /var/www/expense-system/credentials/google-credentials.json

# Check permissions
ls -la /var/www/expense-system/credentials/
```

### Port Already in Use
```bash
# Check what's using port 8000
sudo ss -tlnp | grep 8000

# Kill process if needed
sudo kill <PID>
```

## Security Notes

- SSH access via password (MosesHappy182!)
- Service runs as `helm` user (non-root)
- Google credentials stored securely with 600 permissions
- API keys stored in .env file (not in version control)
- Nginx handles public traffic, application on localhost only

## Backup & Recovery

### Important Files to Backup
1. `/var/www/expense-system/backend/.env` - Environment config
2. `/var/www/expense-system/credentials/google-credentials.json` - Service account
3. `/etc/systemd/system/expense-api.service` - Service definition
4. `/etc/nginx/sites-available/expense-system` - Nginx config

### Quick Backup Command
```bash
ssh helm@77.42.37.42 'tar -czf ~/expense-system-backup-$(date +%Y%m%d).tar.gz /var/www/expense-system/backend/.env /var/www/expense-system/credentials/'
```

## Future Enhancements

- [ ] Enable Telegram notifications
- [ ] Add SSL/HTTPS with Let's Encrypt
- [ ] Set up automated backups
- [ ] Configure monitoring alerts
- [ ] Add log rotation
- [ ] Performance optimization

## Support & Maintenance

**Managed by:** Claude (Automated SSH access via paramiko)
**Management Tool:** `C:\Users\ASUS\vps_manager.py`
**Last Updated:** 2026-03-14

---

For immediate support, run: `python vps_manager.py monitor`
