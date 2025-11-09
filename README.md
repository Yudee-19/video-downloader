# YouTube & Instagram Downloader - Full Stack Application

A full-stack video downloader application built with **React** (frontend) and **FastAPI** (backend) using **yt-dlp**. Download videos and audio from YouTube and Instagram with ease!

## ✨ NEW: Batch Downloads with Redis!

- 🚀 **Download multiple videos simultaneously** (up to 3 in parallel)
- 📊 **Real-time progress tracking** for each video
- 💾 **Redis state management** - persistent across restarts
- ⚡ **Smart queue system** - efficient parallel processing
- 🎯 **Batch up to 10 URLs** at once

## 🎯 Core Features

- ✅ Download YouTube videos in best quality
- ✅ Download Instagram reels and videos
- ✅ Download audio-only (MP3 format) from both platforms
- ✅ Trim YouTube videos with start/end time
- ✅ **Batch downloads** - multiple videos at once
- ✅ Real-time download status updates
- ✅ Modern, responsive UI with batch management
- ✅ CORS-enabled API
- ✅ Background processing for non-blocking downloads
- ✅ Redis-backed state persistence

## 🏗️ Architecture

```
┌──────────────────────────────┐
│          React App           │
│  (URL + time inputs + UI)    │
└─────────────┬────────────────┘
              │  (POST /download)
              ▼
┌──────────────────────────────┐
│         FastAPI Server       │
│  (Handles routes + yt-dlp)   │
└─────────────┬────────────────┘
              │
     yt-dlp downloads video
              │
              ▼
┌──────────────────────────────┐
│  Temp storage (/tmp_videos)  │
│  File saved as .mp4          │
└─────────────┬────────────────┘
              │
  (Return file path or download link)
              ▼
┌──────────────────────────────┐
│       React App (Client)     │
│ Shows "Download Ready" link  │
│   fetches via GET /video/:id │
└──────────────────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **yt-dlp** - YouTube video downloader
- **uvicorn** - ASGI server
- **Python 3.8+**

### Frontend
- **React 18** - UI library
- **Axios** - HTTP client
- **CSS3** - Styling

## 📁 Project Structure

```
youtube-downloader/
│
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── tmp_videos/          # Downloaded videos storage
│   └── .gitignore
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── DownloadForm.js
│   │   │   ├── DownloadForm.css
│   │   │   ├── DownloadStatus.js
│   │   │   └── DownloadStatus.css
│   │   ├── App.js
│   │   ├── App.css
│   │   ├── index.js
│   │   └── index.css
│   ├── package.json
│   └── .gitignore
│
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- npm or yarn
- ffmpeg (optional, for video trimming)
- **Redis** (for batch downloads)

### Quick Start with Redis

**Docker (Recommended)**:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**Or use start scripts**:
```bash
# Windows
start-local-redis.bat

# Linux/Mac
./start-local-redis.sh
```

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables:
```bash
export REDIS_HOST=localhost
export REDIS_PORT=6379
export MAX_PARALLEL_DOWNLOADS=3
```

5. Run the FastAPI server:
```bash
uvicorn main:app --reload
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
echo "REACT_APP_API_URL=http://localhost:8000" > .env.development
```

4. Start the development server:
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

## 📡 API Endpoints

### `POST /download`
Start a video download
```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "start_time": "00:00:30",  // optional
  "end_time": "00:02:00",    // optional
  "audio_only": false        // optional
}
```

**Response:**
```json
{
  "file_id": "uuid-string",
  "message": "Download started"
}
```

### `GET /status/{file_id}`
Check download status

**Response:**
```json
{
  "ready": true,
  "filename": "video.mp4",
  "error": null,
  "progress": "100%",
  "status": "completed"
}
```

### `GET /video/{file_id}`
Download the completed video file

### `DELETE /cleanup/{file_id}`
Remove downloaded file from server

### `POST /batch-download` ✨ NEW
Start batch download of multiple videos

**Request:**
```json
{
  "urls": [
    "https://youtube.com/watch?v=xxx",
    "https://youtube.com/watch?v=yyy"
  ],
  "audio_only": false
}
```

**Response:**
```json
{
  "batch_id": "uuid",
  "download_ids": ["uuid1", "uuid2"],
  "message": "Started batch download of 2 videos"
}
```

### `GET /batch-status/{batch_id}` ✨ NEW
Check status of all downloads in a batch

**Response:**
```json
{
  "batch_id": "uuid",
  "total": 2,
  "completed": 1,
  "failed": 0,
  "in_progress": 1,
  "downloads": [...]
}
```

## 💡 Usage

### Single Download
1. Open the application at `http://localhost:3000`
2. Enter a YouTube URL
3. (Optional) Set start and end times for trimming
4. (Optional) Check "Audio Only" for MP3 download
5. Click "Download"
6. Wait for the download to complete
7. Click "Download File" to save to your device

### Batch Download ✨ NEW
1. Click the **"Batch Download"** tab
2. Enter multiple YouTube/Instagram URLs (up to 10)
3. Add more fields with the **"+"** button
4. (Optional) Enable "Audio Only" for all videos
5. Click **"Download All"**
6. Watch real-time progress for each video
7. Download completed videos individually

## 🎨 Features Explained

### Video Download
- Downloads in best available quality
- Automatically merges video and audio streams
- **Parallel processing** for batch downloads

### Audio-Only Mode
- Extracts audio and converts to MP3
- Quality: 192kbps
- Works for both single and batch downloads

### Trimming (Requires ffmpeg)
- Specify start and end times
- Format: `HH:MM:SS` or seconds
- Uses lossless copy when possible

### Batch Downloads ✨ NEW
- Download up to 10 videos at once
- 3 videos download in parallel (configurable)
- Individual progress tracking
- Redis-backed state management
- Survives server restarts

### Status Polling
- Checks download status every 2 seconds
- Shows real-time progress with percentage
- Handles errors gracefully
- Batch statistics dashboard

## 🔧 Configuration

### Backend Configuration

Environment variables:
```bash
REDIS_HOST=localhost          # Redis server host
REDIS_PORT=6379              # Redis port
REDIS_PASSWORD=              # Redis password (optional)
MAX_PARALLEL_DOWNLOADS=3     # Concurrent downloads
CORS_ORIGINS=*               # Allowed origins
TEMP_DIR=/data/tmp_videos    # Storage location
```

Edit `backend/main.py` to customize:
- Download formats - Modify `ydl_opts`
- User agents - Update `USER_AGENTS` list
- Cleanup policies

### Frontend Configuration

Environment variables:
```bash
REACT_APP_API_URL=http://localhost:8000  # Backend URL
```

## 🚀 Production Deployment

### Option 1: Render (Recommended - Simpler & Cheaper)

**Cost**: ~$37/month | **Setup**: 5 minutes

1. Push code to GitHub
2. Use included `render.yaml`
3. Deploy with one click
4. Redis included & managed

**📚 Complete guide**: [RENDER_DEPLOYMENT_GUIDE.md](./RENDER_DEPLOYMENT_GUIDE.md)

```bash
# Quick deploy
git add render.yaml
git push
# Go to Render → New → Blueprint → Apply
```

### Option 2: AWS (Enterprise Scale)

**Cost**: ~$83/month | **Setup**: 2-3 hours

1. Deploy CloudFormation stack (includes Redis)
2. Build and push Docker image to ECR
3. Create ECS service
4. Deploy frontend to S3 + CloudFront

**📚 Complete guide**: [REDIS_DEPLOYMENT_GUIDE.md](./REDIS_DEPLOYMENT_GUIDE.md)

```bash
# Quick deploy
aws cloudformation create-stack \
    --stack-name ytdlp-infrastructure \
    --template-body file://aws/cloudformation-template.yaml \
    --capabilities CAPABILITY_IAM
```

### Comparison

| Feature | Render | AWS |
|---------|--------|-----|
| **Cost** | $37/month | $83/month |
| **Setup Time** | 5 minutes | 2-3 hours |
| **Complexity** | Simple | Complex |
| **Scale** | Good | Unlimited |
| **Recommendation** | ✅ Start here | Scale later |

**📊 Full comparison**: [AWS_VS_RENDER.md](./AWS_VS_RENDER.md)

### Manual Deployment

#### Backend

1. Set up a production server (e.g., DigitalOcean, AWS, Render)
2. Install Redis
3. Install dependencies
4. Use a production ASGI server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

5. Use a process manager like systemd or supervisor
6. Set up nginx as a reverse proxy

#### Frontend

1. Build the React app:
```bash
npm run build
```

2. Serve the `build` folder with nginx or any static hosting
3. Update `API_URL` to point to production backend

## 🛡️ Security Considerations

- ⚠️ This is a demo application
- Add rate limiting for production use
- Implement user authentication
- Add file size limits
- Set up automatic cleanup of old files
- Validate URLs more thoroughly
- Use HTTPS in production
- Secure Redis with password (production)

## 🐛 Troubleshooting

### Redis connection failed
- **Local**: Ensure Redis is running (`redis-cli ping`)
- **Production**: Check Redis endpoint and security groups
- **Solution**: Use `start-local-redis.bat` or Docker

### "Download failed" error
- Check if the YouTube URL is valid
- Ensure yt-dlp is up to date: `pip install -U yt-dlp`
- Some videos may be restricted
- Check cookies.txt for Instagram

### Batch downloads not parallel
- Verify `MAX_PARALLEL_DOWNLOADS` is set
- Check available CPU/memory
- Review logs for threading activity

### Trimming not working
- Install ffmpeg: `sudo apt install ffmpeg` (Linux) or `brew install ffmpeg` (Mac)
- On Windows, download from https://ffmpeg.org/

### CORS errors
- Ensure backend is running on port 8000
- Check CORS configuration in `main.py`
- Update `CORS_ORIGINS` with your frontend URL

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [RENDER_DEPLOYMENT_GUIDE.md](./RENDER_DEPLOYMENT_GUIDE.md) | Deploy to Render (recommended) |
| [REDIS_DEPLOYMENT_GUIDE.md](./REDIS_DEPLOYMENT_GUIDE.md) | Deploy to AWS with Redis |
| [AWS_VS_RENDER.md](./AWS_VS_RENDER.md) | Platform comparison |
| [README_BATCH_DOWNLOADS.md](./README_BATCH_DOWNLOADS.md) | Batch features documentation |
| [BATCH_DOWNLOAD_SUMMARY.md](./BATCH_DOWNLOAD_SUMMARY.md) | Implementation summary |
| [QUICK_COMMANDS.md](./QUICK_COMMANDS.md) | Command reference |

## 📝 License

This project is for educational purposes only. Respect YouTube's Terms of Service and copyright laws.

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## ✨ What's New (v2.0)

- ✅ **Batch Downloads** - Download multiple videos at once
- ✅ **Parallel Processing** - 3 concurrent downloads
- ✅ **Redis Integration** - Persistent state management
- ✅ **Real-time Progress** - Individual video tracking
- ✅ **Render Support** - Simpler deployment option
- ✅ **Enhanced UI** - Batch management dashboard
- ✅ **Auto-deployment** - Git push to deploy

## 🔮 Future Enhancements

- [ ] WebSocket for real-time updates (no polling)
- [ ] Playlist support (download entire playlists)
- [ ] User accounts and download history
- [ ] Cloud storage integration (S3, GCS)
- [ ] Subtitle download support
- [ ] Quality selection options
- [ ] Email notifications
- [ ] Scheduled downloads
- [ ] Rate limiting per user
- [ ] Authentication & authorization

## 📧 Support

For issues or questions, please open an issue on the repository.

---

Built with ❤️ using React, FastAPI, yt-dlp, and Redis

**⭐ Star this repo if you find it useful!**
