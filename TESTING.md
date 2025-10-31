# Testing Guide - Instagram & Audio Fix

## 🧪 Quick Test Checklist

### 1. Test Audio-Only Download (Bug Fix Verification)

**Before the fix**: Audio downloads would fail with "File not found" error
**After the fix**: Audio should download successfully as MP3

#### Test Steps:
1. Start both backend and frontend servers
2. Go to http://localhost:3000
3. Enter any YouTube URL (e.g., `https://www.youtube.com/watch?v=dQw4w9WgXcQ`)
4. ✅ Check the "Audio Only (MP3)" checkbox
5. Click "Download"
6. Wait for download to complete
7. Click "Download File"
8. **Expected**: File downloads successfully as .mp3
9. **Verify**: Audio file plays correctly

### 2. Test Instagram Reel Download

**New Feature**: Download Instagram reels and videos

#### Test Steps:
1. Go to http://localhost:3000
2. Find a public Instagram reel URL
   - Example format: `https://www.instagram.com/reel/ABC123def456/`
   - Or: `https://www.instagram.com/p/ABC123def456/` (for posts)
3. Paste the URL
4. Click "Download"
5. Wait for download to complete
6. Click "Download File"
7. **Expected**: Video downloads successfully as .mp4
8. **Verify**: Video plays correctly

### 3. Test Instagram Audio-Only

Combine both new features:

#### Test Steps:
1. Go to http://localhost:3000
2. Enter an Instagram reel/video URL
3. ✅ Check the "Audio Only (MP3)" checkbox
4. Click "Download"
5. Wait for completion
6. Download and verify audio file

### 4. Test YouTube Video (Original Functionality)

Ensure existing features still work:

#### Test Steps:
1. Enter a YouTube video URL
2. Leave "Audio Only" unchecked
3. Click "Download"
4. **Expected**: Video downloads as .mp4

### 5. Test YouTube Video Trimming

Ensure trimming still works:

#### Test Steps:
1. Enter a YouTube video URL
2. Set Start Time: `10` (10 seconds)
3. Set End Time: `20` (20 seconds)
4. Click "Download"
5. **Expected**: 10-second trimmed video downloads
6. **Note**: Requires FFmpeg installed

## 🔍 API Testing with Curl

### Test 1: YouTube Audio Download
```bash
# Start download
curl -X POST http://localhost:8000/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw", "audio_only": true}'

# Response will give you a file_id
# {"file_id":"abc-123-def","message":"Download started"}

# Check status (replace FILE_ID with actual id)
curl http://localhost:8000/status/FILE_ID

# Download file when ready
curl -O http://localhost:8000/video/FILE_ID
```

### Test 2: Instagram Reel Download
```bash
# Replace with actual Instagram URL
curl -X POST http://localhost:8000/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/reel/XXXXXXXXX/", "audio_only": false}'

# Check status
curl http://localhost:8000/status/FILE_ID

# Download when ready
curl -O http://localhost:8000/video/FILE_ID
```

### Test 3: Check API Health
```bash
curl http://localhost:8000/

# Expected response:
# {
#   "message": "YouTube & Instagram Downloader API",
#   "status": "running",
#   "supported_platforms": ["YouTube", "Instagram"]
# }
```

## 📊 Test Results Template

Use this template to document your testing:

```markdown
### Test Results - [Date]

#### Audio Download Fix
- [ ] YouTube audio-only download: ✅ Pass / ❌ Fail
- [ ] Instagram audio-only download: ✅ Pass / ❌ Fail
- [ ] Audio file plays correctly: ✅ Pass / ❌ Fail

#### Instagram Support
- [ ] Instagram reel download: ✅ Pass / ❌ Fail
- [ ] Instagram video post download: ✅ Pass / ❌ Fail
- [ ] URL validation works: ✅ Pass / ❌ Fail

#### Existing Features
- [ ] YouTube video download: ✅ Pass / ❌ Fail
- [ ] Video trimming: ✅ Pass / ❌ Fail
- [ ] Status polling: ✅ Pass / ❌ Fail
- [ ] File serving: ✅ Pass / ❌ Fail

#### Notes:
- Any issues encountered:
- Browser: 
- OS: 
```

## 🐛 Common Issues & Solutions

### Issue 1: "File not found" for audio downloads
**Status**: ✅ FIXED in this update
**Solution**: Audio file extension tracking was corrected in the backend

### Issue 2: Instagram private content
**Expected Behavior**: Instagram private accounts/content cannot be downloaded
**Solution**: Use public Instagram content only

### Issue 3: FFmpeg not installed
**Symptoms**: Audio extraction fails, trimming doesn't work
**Solution**: Install FFmpeg:
- Windows: Download from https://ffmpeg.org/
- Mac: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

### Issue 4: Instagram URL not recognized
**Check**: Ensure URL includes "instagram.com"
**Valid formats**:
- `https://www.instagram.com/reel/ABC123/`
- `https://www.instagram.com/p/ABC123/`
- `https://instagram.com/reel/ABC123/`

## ✅ Success Criteria

All tests should pass with these results:

1. ✅ Audio-only downloads create .mp3 files
2. ✅ Audio files download without "file not found" errors
3. ✅ Instagram URLs are accepted by the form
4. ✅ Instagram reels/videos download successfully
5. ✅ YouTube downloads still work as before
6. ✅ Video trimming still works (with FFmpeg)
7. ✅ Status polling shows correct progress
8. ✅ UI shows both platform names

## 📝 Report Issues

If you find any issues:

1. Note the exact error message
2. Check browser console (F12)
3. Check backend terminal output
4. Note the URL that failed
5. Note which platform (YouTube/Instagram)
6. Note if audio-only was selected

Example issue report:
```
Platform: Instagram
URL: https://www.instagram.com/reel/ABC123/
Audio Only: Yes
Error: [exact error message]
Browser Console: [any errors]
Backend Log: [any errors]
```

---

**Happy Testing! 🚀**

If all tests pass, your application now supports:
- ✅ YouTube video downloads
- ✅ Instagram video downloads  
- ✅ Audio extraction from both platforms
- ✅ Fixed audio file download bug
