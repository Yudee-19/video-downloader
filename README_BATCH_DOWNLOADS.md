# 🎬 YouTube & Instagram Downloader - Multiple Downloads Edition

A production-ready video downloader with **batch download support**, **Redis-backed state management**, and **parallel processing**.

## ✨ Features

### Core Features
- ✅ Download YouTube videos and Instagram reels
- ✅ Audio-only download (MP3 extraction)
- ✅ Video trimming (start/end time)
- ✅ Video preview (YouTube)
- ✅ Beautiful dark-themed UI

### New: Batch Download Features
- 🚀 **Parallel Downloads**: Download up to 3 videos simultaneously
- 📊 **Real-time Progress**: Individual progress tracking for each video
- 🎯 **Batch Management**: Add up to 10 URLs at once
- 💾 **Redis State**: Persistent state across server restarts
- ⚡ **Queue System**: Smart queuing and parallel execution
- 📈 **Batch Statistics**: See total, completed, failed, and in-progress downloads

## 🏗️ Architecture

```
Frontend (React)
    ↓
CloudFront CDN
    ↓
Application Load Balancer
    ↓
ECS Fargate (1-2 vCPU, 2-4 GB RAM)
    ├── FastAPI Backend
    ├── ThreadPoolExecutor (3 workers)
    └── yt-dlp
    ↓
├── Redis (ElastiCache) - State storage
└── EFS - Temporary video files
```

## 📋 Prerequisites

- AWS Account
- AWS CLI configured
- Docker Desktop
- Node.js 16+
- Python 3.9+
- Redis (for local testing)

## 🚀 Quick Start

### Local Development

1. **Start Redis**:
```bash
# Windows (WSL)
wsl sudo service redis-server start

# Mac
brew services start redis

# Docker
docker run -d -p 6379:6379 redis:7-alpine
```

2. **Run with one command**:
```bash
# Linux/Mac
chmod +x start-local-redis.sh
./start-local-redis.sh

# Windows
start-local-redis.bat
```

3. **Manual start**:
```bash
# Backend
cd backend
pip install -r requirements.txt
export REDIS_HOST=localhost
export REDIS_PORT=6379
python main.py

# Frontend
cd frontend
npm install
echo "REACT_APP_API_URL=http://localhost:8000" > .env.development
npm start
```

4. **Open** http://localhost:3000

### AWS Deployment

See **[REDIS_DEPLOYMENT_GUIDE.md](./REDIS_DEPLOYMENT_GUIDE.md)** for complete deployment instructions.

**Quick deploy**:
```bash
# 1. Deploy infrastructure (includes Redis)
aws cloudformation create-stack \
    --stack-name ytdlp-infrastructure \
    --template-body file://aws/cloudformation-template.yaml \
    --capabilities CAPABILITY_IAM

# 2. Build and push Docker image
cd backend
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
docker build -t ytdlp-backend .
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/ytdlp-backend:latest

# 3. Deploy ECS service (see guide for details)
```

## 🎯 Usage

### Single Download
1. Go to the app
2. Paste YouTube or Instagram URL
3. (Optional) Set start/end time for trimming
4. (Optional) Enable "Audio Only"
5. Click "Download"

### Batch Download
1. Click **"Batch Download"** tab
2. Enter multiple URLs (up to 10)
3. (Optional) Enable "Audio Only" for all
4. Click **"Download All"**
5. Watch real-time progress for each video
6. Download completed videos individually

## 🔧 Configuration

### Backend Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REDIS_HOST` | Redis server hostname | localhost | Yes |
| `REDIS_PORT` | Redis server port | 6379 | No |
| `REDIS_PASSWORD` | Redis password | None | No |
| `MAX_PARALLEL_DOWNLOADS` | Concurrent downloads | 3 | No |
| `CORS_ORIGINS` | Allowed origins | * | Yes |
| `TEMP_DIR` | Video storage path | tmp_videos | No |

### Adjusting Parallel Downloads

To change the number of concurrent downloads:

1. **Local**:
```bash
export MAX_PARALLEL_DOWNLOADS=5
```

2. **AWS** (edit `aws/ecs-task-definition.json`):
```json
{
  "name": "MAX_PARALLEL_DOWNLOADS",
  "value": "5"
}
```

**Note**: Higher parallelism requires more CPU/memory. Recommended:
- 3 parallel: 1 vCPU, 2 GB RAM
- 5 parallel: 2 vCPU, 4 GB RAM

## 📡 API Endpoints

### Single Download
```bash
# Start download
POST /download
{
  "url": "https://youtube.com/watch?v=xxx",
  "start_time": "00:00:10",  # optional
  "end_time": "00:01:00",    # optional
  "audio_only": false         # optional
}

# Check status
GET /status/{file_id}

# Download file
GET /video/{file_id}

# Cleanup
DELETE /cleanup/{file_id}
```

### Batch Download
```bash
# Start batch
POST /batch-download
{
  "urls": [
    "https://youtube.com/watch?v=xxx",
    "https://youtube.com/watch?v=yyy"
  ],
  "audio_only": false
}

# Check batch status
GET /batch-status/{batch_id}

# Cleanup batch
DELETE /batch-cleanup/{batch_id}
```

## 🧪 Testing

### Test Single Download
```bash
curl -X POST http://localhost:8000/download \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Test Batch Download
```bash
curl -X POST http://localhost:8000/batch-download \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "https://www.youtube.com/watch?v=9bZkp7q19f0"
    ]
  }'
```

### Verify Parallel Processing
```bash
# Watch logs while batch downloading
python -c "
import requests
import time

# Start batch download
response = requests.post('http://localhost:8000/batch-download', json={
    'urls': [
        'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'https://www.youtube.com/watch?v=9bZkp7q19f0',
        'https://www.youtube.com/watch?v=kJQP7kiw5Fk'
    ]
})

batch_id = response.json()['batch_id']
print(f'Batch ID: {batch_id}')

# Poll status
while True:
    status = requests.get(f'http://localhost:8000/batch-status/{batch_id}').json()
    print(f'Progress: {status[\"completed\"]}/{status[\"total\"]} - In progress: {status[\"in_progress\"]}')
    if status['in_progress'] == 0:
        break
    time.sleep(2)
"
```

## 🐛 Troubleshooting

### Redis Connection Failed
```bash
# Check Redis is running
redis-cli ping

# Should return: PONG

# If not running:
# Windows WSL: wsl sudo service redis-server start
# Mac: brew services start redis
# Linux: sudo systemctl start redis
# Docker: docker run -d -p 6379:6379 redis:7-alpine
```

### Backend Not Starting
```bash
# Check logs
tail -f backend/logs.txt

# Common issues:
# - Redis not running
# - Port 8000 already in use
# - Missing dependencies

# Solutions:
pip install -r backend/requirements.txt
lsof -ti:8000 | xargs kill -9  # Kill process on port 8000
```

### Downloads Failing
```bash
# Update yt-dlp
pip install --upgrade yt-dlp

# Check cookies.txt is present
ls backend/cookies.txt

# Test yt-dlp directly
yt-dlp --cookies backend/cookies.txt "https://youtube.com/watch?v=xxx"
```

### High Memory Usage
- Reduce `MAX_PARALLEL_DOWNLOADS` to 2 or 1
- Increase ECS task memory
- Enable EFS cleanup cron job

## 💰 AWS Cost Estimate

| Service | Configuration | Monthly Cost |
|---------|---------------|--------------|
| ECS Fargate | 1 vCPU, 2 GB | ~$30 |
| ElastiCache Redis | t3.micro | ~$12 |
| ALB | 1 load balancer | ~$16 |
| EFS | 20 GB | ~$6 |
| S3 + CloudFront | 100 GB | ~$9 |
| **Total** | | **~$73/month** |

**Cost Optimization**:
- Auto-scale ECS to 0 during off-hours
- Use Fargate Spot (70% discount)
- Enable EFS lifecycle policies
- Set S3 lifecycle rules

## 📊 Performance

### Benchmarks
- **Single download**: 30-120 seconds (depends on video size)
- **Batch download (3 videos)**: Same as single (parallel)
- **Max throughput**: ~3 videos/minute with 3 workers
- **Memory usage**: ~200-500 MB per download
- **EFS throughput**: Sufficient for HD videos

### Scaling
- **Vertical**: Increase task CPU/memory for more parallel downloads
- **Horizontal**: Scale ECS service to 2+ tasks (Redis handles state)
- **Redis**: Can handle 1000s of downloads tracked simultaneously

## 🔒 Security

- CORS configured for specific domains
- HTTPS via CloudFront
- Security groups restrict access
- No exposed Redis port (VPC only)
- EFS encryption at rest
- IAM roles for ECS tasks

## 📚 Project Structure

```
ytdlp-demo/
├── backend/
│   ├── main.py              # FastAPI app with Redis & threading
│   ├── requirements.txt     # Python dependencies (+ redis)
│   ├── Dockerfile          # Backend container
│   └── cookies.txt         # Instagram cookies
├── frontend/
│   ├── src/
│   │   ├── App.js                      # Main app with mode toggle
│   │   └── components/
│   │       ├── DownloadForm.js         # Single download
│   │       ├── DownloadStatus.js       # Single status
│   │       ├── BatchDownloadForm.js    # Batch download (NEW)
│   │       └── BatchDownloadStatus.js  # Batch status (NEW)
│   ├── package.json
│   └── Dockerfile
├── aws/
│   ├── cloudformation-template.yaml    # Infrastructure (+ Redis)
│   └── ecs-task-definition.json       # ECS config (+ Redis vars)
├── REDIS_DEPLOYMENT_GUIDE.md          # Complete deployment guide
├── start-local-redis.sh               # Local start script
└── start-local-redis.bat              # Windows start script
```

## 🚀 What's Next?

- [ ] Add authentication (JWT)
- [ ] Implement rate limiting
- [ ] Store download history in Redis
- [ ] WebSocket for real-time updates
- [ ] Move videos to S3 instead of EFS
- [ ] Add video playlist support
- [ ] Implement scheduled downloads
- [ ] Add email notifications

## 📖 Documentation

- [Complete Deployment Guide](./REDIS_DEPLOYMENT_GUIDE.md)
- [Original Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Quick Start Commands](./DEPLOYMENT_QUICKSTART.md)
- [API Documentation](http://localhost:8000/docs) (when running)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is for educational purposes. Respect YouTube's and Instagram's Terms of Service.

## 🙏 Credits

- **yt-dlp**: Video downloading
- **FastAPI**: Backend framework
- **React**: Frontend framework
- **Redis**: State management
- **AWS**: Cloud infrastructure

---

**Made with ❤️ for parallel downloading**

For questions or issues, check the [Deployment Guide](./REDIS_DEPLOYMENT_GUIDE.md) or open an issue.
