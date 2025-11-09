# 🚀 Render Deployment Guide - Multiple Downloads Edition

Deploy your YouTube Downloader with Redis and batch downloads on **Render** - simpler and potentially cheaper than AWS!

---

## 🎯 Why Render?

### Advantages over AWS:
- ✅ **Much Simpler** - No CloudFormation, security groups, or VPC configuration
- ✅ **Managed Redis** - Built-in Redis with automatic backups
- ✅ **Auto-Deploy** - Git push automatically deploys
- ✅ **Free SSL** - Automatic HTTPS certificates
- ✅ **Better Pricing** - Potentially cheaper for small-medium workloads
- ✅ **No Cold Starts** - Unlike AWS Lambda
- ✅ **Easy Scaling** - Simple slider to scale resources

### What Works on Render:
- ✅ Backend with FastAPI
- ✅ Redis for state management
- ✅ Batch downloads (all features)
- ✅ Parallel processing
- ✅ Persistent storage (disk volumes)
- ✅ Frontend on Render or keep on AWS CloudFront

---

## 💰 Cost Comparison

### Render Pricing:

| Service | Plan | Cost |
|---------|------|------|
| **Web Service** (Backend) | Starter (512MB RAM, 0.5 CPU) | $7/month |
| **Web Service** (Backend) | Standard (2GB RAM, 1 CPU) | $25/month |
| **Redis** | 25MB (Free) | $0 |
| **Redis** | 100MB | $10/month |
| **Disk Storage** | 1 GB | $0.25/month |
| **Static Site** (Frontend) | Free | $0 |

**Recommended Setup**: $25 (Standard) + $10 (Redis) + $1 (Disk) = **$36/month**

**AWS Comparison**: ~$78-102/month 😱

**Savings**: ~$42-66/month! 🎉

---

## 📋 Prerequisites

1. **GitHub Account** - Your code must be on GitHub
2. **Render Account** - Sign up at https://render.com (free)
3. **Git Repository** - Push your code to GitHub

---

## 🚀 Step-by-Step Deployment

### Step 1: Prepare Your Code

1. **Create `render.yaml`** (Infrastructure as Code):

```yaml
services:
  # Backend Service
  - type: web
    name: ytdlp-backend
    env: docker
    dockerfilePath: ./backend/Dockerfile
    plan: standard  # Change to 'starter' for $7/month (512MB RAM)
    region: oregon
    branch: main
    healthCheckPath: /
    envVars:
      - key: REDIS_HOST
        fromService:
          type: redis
          name: ytdlp-redis
          property: host
      - key: REDIS_PORT
        fromService:
          type: redis
          name: ytdlp-redis
          property: port
      - key: MAX_PARALLEL_DOWNLOADS
        value: 3
      - key: CORS_ORIGINS
        value: "*"  # Update with your frontend URL later
      - key: TEMP_DIR
        value: /data/tmp_videos
    disk:
      name: video-storage
      mountPath: /data
      sizeGB: 10
    autoDeploy: true

  # Redis Service
  - type: redis
    name: ytdlp-redis
    plan: starter  # 100MB Redis
    region: oregon
    ipAllowList: []  # Allow access from your services

  # Frontend (Optional - or use AWS CloudFront)
  - type: web
    name: ytdlp-frontend
    env: static
    buildCommand: cd frontend && npm install && npm run build
    staticPublishPath: ./frontend/build
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
    envVars:
      - key: REACT_APP_API_URL
        value: https://ytdlp-backend.onrender.com  # Update after backend deploys
```

2. **Update Backend Dockerfile** (if needed):

Your existing `backend/Dockerfile` should work, but ensure it has:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create temp directory
RUN mkdir -p /data/tmp_videos

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

3. **Commit and Push**:

```bash
# Add render.yaml to your project root
git add render.yaml
git commit -m "Add Render deployment configuration"
git push origin main
```

---

### Step 2: Deploy on Render

#### Option A: Using render.yaml (Recommended)

1. Go to https://render.com/dashboard
2. Click **"New"** → **"Blueprint"**
3. Connect your GitHub repository
4. Select the repository with `render.yaml`
5. Click **"Apply"**
6. Render will automatically:
   - Create Redis instance
   - Create backend service
   - Link them together
   - Deploy everything

#### Option B: Manual Setup

1. **Create Redis**:
   - Dashboard → **New** → **Redis**
   - Name: `ytdlp-redis`
   - Plan: **Starter** ($10/month for 100MB)
   - Region: **Oregon**
   - Click **Create Redis**
   - **Copy the Internal Redis URL** (like `redis://red-xxx:6379`)

2. **Create Backend Service**:
   - Dashboard → **New** → **Web Service**
   - Connect your GitHub repo
   - Name: `ytdlp-backend`
   - Region: **Oregon**
   - Branch: **main**
   - Root Directory: `backend`
   - Environment: **Docker**
   - Instance Type: **Standard** (2GB RAM recommended)
   - Add **Disk**:
     - Name: `video-storage`
     - Mount Path: `/data`
     - Size: **10 GB**
   - Add **Environment Variables**:
     ```
     REDIS_HOST=red-xxx.oregon-postgres.render.com
     REDIS_PORT=6379
     MAX_PARALLEL_DOWNLOADS=3
     CORS_ORIGINS=*
     TEMP_DIR=/data/tmp_videos
     ```
   - Click **Create Web Service**

3. **Create Frontend** (Optional):
   - Dashboard → **New** → **Static Site**
   - Connect repo
   - Name: `ytdlp-frontend`
   - Root Directory: `frontend`
   - Build Command: `npm install && npm run build`
   - Publish Directory: `build`
   - Add Environment Variable:
     ```
     REACT_APP_API_URL=https://ytdlp-backend.onrender.com
     ```
   - Click **Create Static Site**

---

### Step 3: Configure Environment Variables

After backend deploys, get its URL (e.g., `https://ytdlp-backend.onrender.com`)

1. **Update Backend CORS**:
   - Go to backend service → **Environment**
   - Update `CORS_ORIGINS`:
     ```
     CORS_ORIGINS=https://ytdlp-frontend.onrender.com,https://your-cloudfront-url.net
     ```

2. **Update Frontend API URL** (if using Render frontend):
   - Go to frontend service → **Environment**
   - Ensure `REACT_APP_API_URL` points to backend:
     ```
     REACT_APP_API_URL=https://ytdlp-backend.onrender.com
     ```
   - Trigger redeploy

---

## 🧪 Testing Your Deployment

### 1. Test Backend Health
```bash
curl https://ytdlp-backend.onrender.com/
```

Should return:
```json
{
  "message": "YouTube & Instagram Downloader API",
  "status": "running",
  "supported_platforms": ["YouTube", "Instagram"]
}
```

### 2. Test Single Download
```bash
curl -X POST https://ytdlp-backend.onrender.com/download \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### 3. Test Batch Download
```bash
curl -X POST https://ytdlp-backend.onrender.com/batch-download \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "https://www.youtube.com/watch?v=9bZkp7q19f0"
    ]
  }'
```

### 4. Test Frontend
Open your frontend URL and try batch downloads!

---

## ⚙️ Configuration

### Scaling Resources

**To handle more parallel downloads**:

1. Go to backend service → **Settings**
2. Change **Instance Type**:
   - **Starter** (512MB): 1-2 parallel downloads
   - **Standard** (2GB): 3 parallel downloads ✅
   - **Pro** (4GB): 5 parallel downloads
   - **Pro Plus** (8GB): 10 parallel downloads

3. Update `MAX_PARALLEL_DOWNLOADS` environment variable accordingly

### Redis Scaling

1. Go to Redis service → **Settings**
2. Upgrade plan if needed:
   - **Starter** (100MB): ~50-100 concurrent downloads tracked
   - **Standard** (1GB): ~500-1000 concurrent downloads tracked

### Disk Storage

Increase disk if videos fill up:
1. Backend service → **Settings** → **Disks**
2. Increase size (billed at $0.25/GB/month)

---

## 🔄 Auto-Deployment (CI/CD)

Render automatically deploys when you push to GitHub!

```bash
# Make changes
git add .
git commit -m "Update features"
git push origin main

# Render automatically:
# 1. Pulls latest code
# 2. Rebuilds Docker image
# 3. Deploys new version
# 4. Zero-downtime deployment
```

**Monitor deployment**: Dashboard → Service → **Events** tab

---

## 📊 Monitoring

### Logs
```bash
# Real-time logs
# Go to: Dashboard → Service → Logs

# Or use Render CLI
render logs ytdlp-backend --tail
```

### Metrics
- Dashboard → Service → **Metrics** tab
- View: CPU, Memory, Request rate, Response time

### Redis Metrics
- Dashboard → Redis → **Metrics** tab
- View: Memory usage, Connections, Commands/sec

---

## 🐛 Troubleshooting

### Backend Won't Start

**Check logs**:
1. Dashboard → Backend Service → **Logs**
2. Look for errors

**Common issues**:
```bash
# Redis connection failed
# Solution: Verify REDIS_HOST environment variable

# Port already in use
# Solution: Ensure Dockerfile uses CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Out of memory
# Solution: Upgrade to Standard or Pro instance
```

### Redis Connection Errors

**Verify connection**:
1. Dashboard → Redis → **Info** tab
2. Copy **Internal Redis URL**
3. Update backend's `REDIS_HOST` and `REDIS_PORT`

**Redis host format**:
- Host: `red-xxxxx.oregon-postgres.render.com`
- Port: `6379`

### Downloads Failing

```bash
# Update yt-dlp in requirements.txt
yt-dlp>=2024.10.0

# Redeploy
git add backend/requirements.txt
git commit -m "Update yt-dlp"
git push
```

### Disk Full

```bash
# Increase disk size in Settings
# Or add cleanup cron job (see below)
```

---

## 🔧 Advanced Configuration

### Add Cleanup Cron Job

Create `backend/cleanup.py`:
```python
import os
import time
from datetime import datetime, timedelta

TEMP_DIR = os.getenv("TEMP_DIR", "/data/tmp_videos")
MAX_AGE_HOURS = 2

def cleanup_old_files():
    now = datetime.now()
    for filename in os.listdir(TEMP_DIR):
        filepath = os.path.join(TEMP_DIR, filename)
        if os.path.isfile(filepath):
            file_age = datetime.fromtimestamp(os.path.getmtime(filepath))
            if now - file_age > timedelta(hours=MAX_AGE_HOURS):
                os.remove(filepath)
                print(f"Deleted old file: {filename}")

if __name__ == "__main__":
    while True:
        cleanup_old_files()
        time.sleep(3600)  # Run every hour
```

**Create Cron Service** on Render:
1. Dashboard → **New** → **Cron Job**
2. Name: `ytdlp-cleanup`
3. Command: `python cleanup.py`
4. Schedule: `0 * * * *` (every hour)

### Add Health Checks

Render automatically uses your `healthCheckPath: /`

To customize, update `main.py`:
```python
@app.get("/health")
async def health_check():
    # Check Redis
    try:
        redis_client.ping()
        redis_status = "healthy"
    except:
        redis_status = "unhealthy"
    
    return {
        "status": "healthy",
        "redis": redis_status,
        "timestamp": datetime.now().isoformat()
    }
```

Update `render.yaml`:
```yaml
healthCheckPath: /health
```

### Environment-Specific Settings

**Production** (Render):
```yaml
envVars:
  - key: ENVIRONMENT
    value: production
  - key: LOG_LEVEL
    value: INFO
```

**Development** (Local):
```bash
export ENVIRONMENT=development
export LOG_LEVEL=DEBUG
```

---

## 🌐 Custom Domain

### Add Your Domain

1. **Backend**:
   - Service → **Settings** → **Custom Domains**
   - Add: `api.yourdomain.com`
   - Update DNS CNAME: `ytdlp-backend.onrender.com`

2. **Frontend**:
   - Service → **Settings** → **Custom Domains**
   - Add: `yourdomain.com`
   - Update DNS CNAME: `ytdlp-frontend.onrender.com`

3. **Update CORS**:
   ```
   CORS_ORIGINS=https://yourdomain.com
   ```

**SSL**: Render automatically provisions free SSL certificates!

---

## 💾 Backup Strategy

### Redis Backups
Render automatically backs up Redis:
- **Frequency**: Daily
- **Retention**: 7 days (Starter), 14 days (Standard)
- **Recovery**: Dashboard → Redis → **Backups** → **Restore**

### Disk Backups
Render provides disk snapshots:
- Dashboard → Service → **Disks** → **Snapshots**
- Manual snapshots anytime
- Restore to new service if needed

---

## 📈 Performance Optimization

### 1. Use Render's CDN
Enable for static assets:
```yaml
# In render.yaml for frontend
headers:
  - path: /static/*
    name: Cache-Control
    value: public, max-age=31536000
```

### 2. Enable Compression
In `main.py`:
```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 3. Connection Pooling
Redis connection is already pooled in our implementation!

---

## 🔄 Migration from AWS to Render

If you already have AWS deployment:

### 1. Export Data from AWS
```bash
# Export Redis data (if any critical state)
redis-cli -h YOUR-AWS-REDIS-ENDPOINT --rdb dump.rdb

# Download videos from EFS (if needed)
aws s3 sync s3://your-bucket/ ./backup/
```

### 2. Deploy to Render
Follow deployment steps above

### 3. Update DNS
- Point your domain from AWS ALB to Render
- Update CloudFront origin (if keeping CF for frontend)

### 4. Decommission AWS
```bash
# Delete ECS service
aws ecs delete-service --cluster ytdlp-cluster --service ytdlp-service --force

# Delete CloudFormation stack
aws cloudformation delete-stack --stack-name ytdlp-infrastructure
```

---

## 🎯 Hybrid Approach (Best of Both)

**Recommended**:
- ✅ **Backend on Render** - Simpler, cheaper
- ✅ **Frontend on AWS CloudFront** - Global CDN, better performance

**Setup**:
1. Deploy backend on Render (as above)
2. Keep frontend on AWS S3 + CloudFront
3. Update frontend env:
   ```
   REACT_APP_API_URL=https://ytdlp-backend.onrender.com
   ```
4. Update backend CORS:
   ```
   CORS_ORIGINS=https://your-cloudfront-domain.net
   ```

**Benefits**:
- Global CDN for frontend
- Simple backend management
- Lower costs
- Easy scaling

---

## 📊 Cost Calculator

### Example Scenarios:

**Light Usage** (< 100 downloads/day):
- Backend: Starter ($7)
- Redis: Free ($0)
- Disk: 1GB ($0.25)
- **Total: $7.25/month** 🎉

**Medium Usage** (500 downloads/day):
- Backend: Standard ($25)
- Redis: Starter ($10)
- Disk: 10GB ($2.50)
- **Total: $37.50/month**

**Heavy Usage** (2000 downloads/day):
- Backend: Pro ($85)
- Redis: Standard ($50)
- Disk: 50GB ($12.50)
- **Total: $147.50/month**

**Compare to AWS**: 40-60% cheaper! 💰

---

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] `render.yaml` created (or manual setup done)
- [ ] Redis service created
- [ ] Backend service created with disk
- [ ] Environment variables configured
- [ ] Frontend deployed (Render or AWS)
- [ ] CORS configured correctly
- [ ] Custom domain added (optional)
- [ ] Test single download
- [ ] Test batch download
- [ ] Monitor logs for errors
- [ ] Set up billing alerts

---

## 🎉 Success!

Your YouTube Downloader with Redis and batch downloads is now running on Render!

**Benefits achieved**:
- ✅ Simpler deployment than AWS
- ✅ Lower costs
- ✅ Auto-deploy on git push
- ✅ Free SSL
- ✅ Managed Redis
- ✅ Easy scaling
- ✅ All batch features working

**Access your app**:
- Backend API: `https://ytdlp-backend.onrender.com`
- API Docs: `https://ytdlp-backend.onrender.com/docs`
- Frontend: `https://ytdlp-frontend.onrender.com` (or your CloudFront URL)

---

## 🚀 Next Steps

1. Test batch downloads thoroughly
2. Monitor resource usage (CPU/Memory/Disk)
3. Set up custom domain
4. Configure backups
5. Add monitoring/alerting
6. Optimize based on usage patterns

---

## 📞 Support

**Render Issues**:
- Docs: https://render.com/docs
- Community: https://community.render.com
- Support: Dashboard → Help

**Check Service Status**:
- https://status.render.com

---

**Enjoy your simpler, cheaper deployment! 🎊**
