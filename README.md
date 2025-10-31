# YouTube & Instagram Downloader - Full Stack Application

A full-stack video downloader application built with **React** (frontend) and **FastAPI** (backend) using **yt-dlp**. Download videos and audio from YouTube and Instagram with ease!

## 🎯 Features

- ✅ Download YouTube videos in best quality
- ✅ Download Instagram reels and videos
- ✅ Download audio-only (MP3 format) from both platforms
- ✅ Trim YouTube videos with start/end time
- ✅ Real-time download status updates
- ✅ Modern, responsive UI
- ✅ CORS-enabled API
- ✅ Background processing for non-blocking downloads

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

4. Run the FastAPI server:
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

3. Start the development server:
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
  "error": null
}
```

### `GET /video/{file_id}`
Download the completed video file

### `DELETE /cleanup/{file_id}`
Remove downloaded file from server

## 💡 Usage

1. Open the application at `http://localhost:3000`
2. Enter a YouTube URL
3. (Optional) Set start and end times for trimming
4. (Optional) Check "Audio Only" for MP3 download
5. Click "Download"
6. Wait for the download to complete
7. Click "Download File" to save to your device

## 🎨 Features Explained

### Video Download
- Downloads in best available quality
- Automatically merges video and audio streams

### Audio-Only Mode
- Extracts audio and converts to MP3
- Quality: 192kbps

### Trimming (Requires ffmpeg)
- Specify start and end times
- Format: `HH:MM:SS` or seconds
- Uses lossless copy when possible

### Status Polling
- Checks download status every 2 seconds
- Shows real-time progress
- Handles errors gracefully

## 🔧 Configuration

### Backend Configuration

Edit `backend/main.py` to customize:
- `TEMP_DIR` - Change storage location
- CORS origins - Add more allowed origins
- Download formats - Modify `ydl_opts`

### Frontend Configuration

Edit `frontend/src/components/DownloadForm.js`:
- `API_URL` - Change backend URL for production

## 🚀 Production Deployment

### Backend

1. Set up a production server (e.g., DigitalOcean, AWS)
2. Install dependencies
3. Use a production ASGI server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

4. Use a process manager like systemd or supervisor
5. Set up nginx as a reverse proxy

### Frontend

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

## 🐛 Troubleshooting

### "Download failed" error
- Check if the YouTube URL is valid
- Ensure yt-dlp is up to date: `pip install -U yt-dlp`
- Some videos may be restricted

### Trimming not working
- Install ffmpeg: `sudo apt install ffmpeg` (Linux) or `brew install ffmpeg` (Mac)
- On Windows, download from https://ffmpeg.org/

### CORS errors
- Ensure backend is running on port 8000
- Check CORS configuration in `main.py`

## 📝 License

This project is for educational purposes only. Respect YouTube's Terms of Service and copyright laws.

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## 🔮 Future Enhancements

- [ ] Playlist support
- [ ] Multiple simultaneous downloads
- [ ] Download queue management
- [ ] Progress bar with percentage
- [ ] User accounts and history
- [ ] Cloud storage integration (S3, GCS)
- [ ] Docker containerization
- [ ] WebSocket for real-time updates
- [ ] Subtitle download support
- [ ] Quality selection options

## 📧 Support

For issues or questions, please open an issue on the repository.

---

Built with ❤️ using React, FastAPI, and yt-dlp
