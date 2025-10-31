# 🚀 Quick Start Guide - YouTube Downloader

## ✅ What's Been Set Up

Your full-stack YouTube downloader application is now ready! Here's what has been created:

### Backend (FastAPI)
- ✅ FastAPI server with all endpoints
- ✅ yt-dlp integration for downloading videos
- ✅ Background task processing
- ✅ CORS configuration for React
- ✅ Python virtual environment configured
- ✅ All dependencies installed

### Frontend (React)
- ✅ React application with modern UI
- ✅ Download form with URL and options
- ✅ Real-time status polling
- ✅ Download management
- ✅ All npm packages installed

## 🎯 How to Run the Application

### Option 1: Using the Start Scripts (Recommended)

**Windows:**
1. Open **TWO** separate terminals
2. In Terminal 1 (Backend):
   ```bash
   ./start-backend.bat
   ```
3. In Terminal 2 (Frontend):
   ```bash
   ./start-frontend.bat
   ```

**Linux/Mac:**
1. Make scripts executable:
   ```bash
   chmod +x start-backend.sh start-frontend.sh
   ```
2. Open **TWO** separate terminals
3. In Terminal 1 (Backend):
   ```bash
   ./start-backend.sh
   ```
4. In Terminal 2 (Frontend):
   ```bash
   ./start-frontend.sh
   ```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
D:/Projects/ytdlp-demo/.venv/Scripts/python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

## 🌐 Access the Application

Once both servers are running:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Interactive Swagger UI)

## 📝 How to Use

1. **Open your browser** and go to `http://localhost:3000`

2. **Enter a YouTube URL** in the input field
   - Example: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`

3. **(Optional) Configure download options:**
   - **Start Time**: Enter time like `00:00:30` or `30` (for 30 seconds)
   - **End Time**: Enter time like `00:02:00` or `120` (for 2 minutes)
   - **Audio Only**: Check this box to download MP3 instead of video

4. **Click "Download"** button

5. **Wait for processing:**
   - You'll see a "Downloading..." status with progress indicator
   - The app polls the backend every 2 seconds for updates

6. **Download your file:**
   - When ready, click the "Download File" button
   - The file will be saved to your Downloads folder

7. **Download another video:**
   - Click "Download Another" to start a new download

## 🔍 API Endpoints Reference

### 1. Health Check
```http
GET http://localhost:8000/
```

### 2. Start Download
```http
POST http://localhost:8000/download
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=...",
  "start_time": "00:00:30",  // optional
  "end_time": "00:02:00",    // optional
  "audio_only": false        // optional
}
```

### 3. Check Status
```http
GET http://localhost:8000/status/{file_id}
```

### 4. Download File
```http
GET http://localhost:8000/video/{file_id}
```

### 5. Cleanup
```http
DELETE http://localhost:8000/cleanup/{file_id}
```

## 🧪 Testing the API

You can test the API using the built-in Swagger UI:

1. Go to `http://localhost:8000/docs`
2. Try the endpoints interactively
3. See request/response schemas

Or use curl:
```bash
# Test health check
curl http://localhost:8000/

# Start a download
curl -X POST http://localhost:8000/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "audio_only": false}'
```

## 📂 Project Structure

```
ytdlp-demo/
│
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── requirements.txt        # Python dependencies
│   ├── tmp_videos/             # Downloaded videos (created automatically)
│   └── .gitignore
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── DownloadForm.js        # URL input form
│   │   │   ├── DownloadForm.css
│   │   │   ├── DownloadStatus.js      # Download progress
│   │   │   └── DownloadStatus.css
│   │   ├── App.js                     # Main app component
│   │   ├── App.css
│   │   ├── index.js
│   │   └── index.css
│   ├── package.json
│   ├── node_modules/
│   └── .gitignore
│
├── .venv/                      # Python virtual environment
├── start-backend.sh/bat        # Backend start script
├── start-frontend.sh/bat       # Frontend start script
├── README.md                   # Full documentation
└── QUICK_START.md             # This file
```

## ⚠️ Troubleshooting

### Backend won't start
- Make sure Python 3.8+ is installed
- Check if port 8000 is available
- Verify virtual environment is activated

### Frontend won't start
- Make sure Node.js is installed
- Try deleting `node_modules` and run `npm install` again
- Check if port 3000 is available

### Downloads failing
- Verify the YouTube URL is valid and accessible
- Some videos may be age-restricted or region-locked
- Update yt-dlp: `pip install -U yt-dlp`

### CORS errors
- Ensure backend is running on port 8000
- Frontend must be on port 3000
- Check browser console for specific errors

### Trimming not working
- Install FFmpeg on your system
- **Windows**: Download from https://ffmpeg.org/
- **Mac**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

## 🎨 Customization

### Change API Port
Edit `backend/main.py` and update uvicorn command

### Change Frontend Port
Create `.env` file in `frontend/` with:
```
PORT=3001
```

### Update API URL for Production
Edit `frontend/src/components/DownloadForm.js` and `DownloadStatus.js`:
```javascript
const API_URL = 'https://your-api-domain.com';
```

### Modify Download Options
Edit `backend/main.py` and update the `ydl_opts` dictionary

## 🔐 Security Notes

⚠️ **This is a development setup!** For production:

- [ ] Add rate limiting
- [ ] Implement authentication
- [ ] Set up HTTPS
- [ ] Configure proper CORS origins
- [ ] Add file size limits
- [ ] Set up automatic cleanup
- [ ] Use environment variables for configuration
- [ ] Add input validation and sanitization

## 🚀 Next Steps

Now that your app is running, you can:

1. **Test it thoroughly** with different YouTube URLs
2. **Customize the UI** - Edit the CSS files for your style
3. **Add features** from the TODO list in README.md
4. **Deploy it** - See README.md for deployment instructions

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)

## 💬 Need Help?

- Check the main `README.md` for detailed documentation
- Look at the code comments in the source files
- Test the API using the Swagger UI at `/docs`

---

**Enjoy your YouTube Downloader! 🎉**
