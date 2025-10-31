# Changelog

## [1.1.0] - 2025-10-31

### ✨ Added
- **Instagram Support**: Download Instagram reels and video posts
- **Audio File Fix**: Fixed bug where audio-only downloads (MP3) were failing with "file not found" error
- Platform detection for YouTube and Instagram URLs
- Updated UI to support both platforms
- Comprehensive documentation updates

### 🐛 Fixed
- **Critical**: Audio-only downloads now properly track the .mp3 file extension after conversion
- File serving now correctly handles both video (.mp4) and audio (.mp3) files
- Background task properly updates filename after FFmpeg post-processing

### 📝 Changed
- Updated frontend validation to accept both YouTube and Instagram URLs
- Modified placeholder text to indicate multi-platform support
- Enhanced API documentation to reflect Instagram support
- Updated all documentation files (README.md, QUICK_START.md, SUMMARY.md, project.md)

### 🔧 Technical Details

#### Backend Changes (`backend/main.py`)
1. **Audio File Extension Handling**:
   ```python
   # For audio only, the file extension changes to .mp3 after post-processing
   if audio_only:
       base_filename = os.path.splitext(filename)[0]
       filename = f"{base_filename}.mp3"
   ```

2. **Instagram Support**:
   - yt-dlp already supports Instagram - no additional configuration needed
   - Updated API endpoint documentation
   - Modified root endpoint to list supported platforms

#### Frontend Changes
1. **URL Validation** (`frontend/src/components/DownloadForm.js`):
   ```javascript
   const isYouTube = url.includes('youtube.com') || url.includes('youtu.be');
   const isInstagram = url.includes('instagram.com');
   ```

2. **UI Updates**:
   - Changed label from "YouTube URL" to "YouTube or Instagram URL"
   - Updated placeholder to show both URL formats
   - Modified app header to reflect multi-platform support

### 📚 Documentation Updates
- ✅ QUICK_START.md - Added Instagram examples and usage instructions
- ✅ SUMMARY.md - Updated feature list and test instructions
- ✅ project.md - Updated architecture and flow diagrams
- ✅ README.md - Updated main description and features

### 🎯 Supported Platforms

#### YouTube
- Regular videos
- YouTube Shorts
- Audio extraction (MP3)
- Video trimming with start/end time
- Best quality download (bestvideo+bestaudio)

#### Instagram
- Reels
- Video posts
- IGTV videos
- Audio extraction (MP3)
- **Note**: Private accounts and stories are not supported

### 🧪 Testing

#### Test YouTube Download:
```bash
curl -X POST http://localhost:8000/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "audio_only": false}'
```

#### Test Instagram Download:
```bash
curl -X POST http://localhost:8000/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/reel/XXXXXXXXX/", "audio_only": false}'
```

#### Test Audio-Only Download:
```bash
curl -X POST http://localhost:8000/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "audio_only": true}'
```

### ⚠️ Important Notes

1. **FFmpeg Required**: Audio extraction and video trimming require FFmpeg to be installed
2. **Instagram Limitations**: 
   - Only public content can be downloaded
   - Stories are not supported
   - Private accounts cannot be accessed
3. **File Cleanup**: Downloaded files remain in `tmp_videos/` until manually cleaned up via DELETE endpoint

### 🚀 Migration Guide

If you're updating from the previous version:

1. **Backend**: Pull latest changes - no breaking changes
2. **Frontend**: Clear browser cache and refresh
3. **Testing**: Try an Instagram URL to verify the new functionality
4. **Audio Downloads**: Previously broken audio downloads should now work correctly

### 📋 Next Steps

Consider adding:
- [ ] TikTok support
- [ ] Twitter/X video support
- [ ] Automatic file cleanup after X hours
- [ ] Download queue system
- [ ] Progress percentage tracking
- [ ] Playlist support for YouTube
- [ ] WebSocket for real-time progress updates

---

## [1.0.0] - Initial Release

### Initial Features
- YouTube video download
- Audio extraction
- Video trimming
- React frontend
- FastAPI backend
- Real-time status polling
