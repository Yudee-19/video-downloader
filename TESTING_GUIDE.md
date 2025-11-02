# 🧪 Quick Test Guide - Bot Detection Fix

## Test Locally Before AWS Deployment

### Step 1: Test Backend with Python (Fast Test)

```bash
# Navigate to backend directory
cd backend

# Install/update dependencies (if needed)
pip install -r requirements.txt

# Start the backend server
uvicorn main:app --reload
```

The server should start at: `http://localhost:8000`

### Step 2: Test the API

**Open a new terminal and test:**

```bash
# Test 1: Check if server is running
curl http://localhost:8000/

# Expected response:
# {"message":"YouTube & Instagram Downloader API","status":"running","supported_platforms":["YouTube","Instagram"]}

# Test 2: Download a YouTube video
curl -X POST http://localhost:8000/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"}'

# Expected response (save the file_id):
# {"file_id":"<some-uuid>","message":"Download started"}

# Test 3: Check download status (replace FILE_ID)
curl http://localhost:8000/status/<FILE_ID>

# Expected response (when ready):
# {"ready":true,"filename":"video.mp4","error":null}
```

### Step 3: Verify Cookies and Headers

Check the logs - you should see:
- Random User-Agent being used
- No "Sign in to confirm you're not a bot" errors
- Successful download

---

## Test with Docker (Closer to AWS Environment)

### Build and Run Docker Container

```bash
# Navigate to backend directory
cd backend

# Build the Docker image
docker build -t ytdlp-backend-test:latest .

# Run the container
docker run -p 8000:8000 ytdlp-backend-test:latest

# In another terminal, test the same way as above
curl http://localhost:8000/
```

### Verify Cookies in Container

```bash
# Get container ID
docker ps

# Check if cookies.txt exists and is readable
docker exec -it <CONTAINER_ID> ls -la /app/cookies.txt

# Expected output:
# -rw-r--r-- 1 root root 2345 Nov 2 10:00 /app/cookies.txt

# Check cookies content
docker exec -it <CONTAINER_ID> cat /app/cookies.txt | head -5
```

---

## Expected Behavior

### ✅ Success Indicators:
1. Server starts without errors
2. `/download` endpoint returns a `file_id`
3. `/status/<file_id>` eventually shows `ready: true`
4. No "bot detection" errors in logs
5. Video downloads successfully

### ❌ Common Issues:

#### Issue 1: "cookiefile not found"
```bash
# Check if cookies.txt exists
ls -la backend/cookies.txt

# If missing, it should already be in your repo
# Make sure you're in the right directory
```

#### Issue 2: "Sign in to confirm you're not a bot" still appears
```bash
# Your cookies might be expired
# Solution: Export fresh cookies from your browser
# 1. Install "Get cookies.txt LOCALLY" extension
# 2. Visit youtube.com (logged in)
# 3. Export cookies
# 4. Replace backend/cookies.txt
```

#### Issue 3: Permission denied
```bash
# Fix file permissions
chmod 644 backend/cookies.txt
```

---

## Once Local Testing Passes

### Deploy to AWS

**Method 1: Using Git (Automatic CI/CD)**
```bash
# Commit changes
git add backend/main.py backend/Dockerfile IMPLEMENTATION_SUMMARY.md
git commit -m "Fix: Add cookies and randomized User-Agent to bypass YouTube bot detection"
git push origin main

# GitHub Actions will automatically deploy to AWS
# Monitor at: https://github.com/YOUR_USERNAME/ytdlp-demo/actions
```

**Method 2: Manual Docker Push to ECR**
```bash
# Login to AWS ECR
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build for production
cd backend
docker build -t ytdlp-backend:latest .

# Tag image
docker tag ytdlp-backend:latest \
    YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ytdlp-backend:latest

# Push to ECR
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ytdlp-backend:latest

# Force ECS to use new image
aws ecs update-service \
    --cluster ytdlp-cluster \
    --service ytdlp-service \
    --force-new-deployment \
    --region us-east-1
```

---

## Monitoring AWS Deployment

### Check ECS Service Status
```bash
# Check if service is running
aws ecs describe-services \
    --cluster ytdlp-cluster \
    --services ytdlp-service \
    --region us-east-1

# Check task status
aws ecs list-tasks \
    --cluster ytdlp-cluster \
    --service-name ytdlp-service \
    --region us-east-1
```

### View CloudWatch Logs
```bash
# Tail logs in real-time
aws logs tail /ecs/ytdlp-backend --follow --region us-east-1

# Or view in AWS Console:
# CloudWatch > Log groups > /ecs/ytdlp-backend
```

### Test Production Deployment
```bash
# Test with ALB URL
curl -X POST http://YOUR-ALB-URL.amazonaws.com/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"}'
```

---

## 📊 What Changed?

### Code Changes Summary:

| File | Changes |
|------|---------|
| `backend/main.py` | ✅ Added `import random`<br>✅ Added `USER_AGENTS` list<br>✅ Added `COOKIES_FILE` path<br>✅ Updated `download_video_task()` with cookies & headers |
| `backend/Dockerfile` | ✅ Added `chmod 644 /app/cookies.txt` |

### What These Changes Do:

1. **Cookies**: Authenticate with YouTube (bypass bot detection)
2. **Random User-Agent**: Each request uses a different browser identity
3. **Retries**: More resilient downloads with 5 retry attempts

---

## 🎯 Next Steps

1. ✅ Test locally using the commands above
2. ✅ If tests pass, commit and push to GitHub
3. ✅ Monitor GitHub Actions deployment
4. ✅ Test production URL
5. ✅ Verify downloads work without bot errors

---

## 📞 Need Help?

If you encounter issues:

1. Check logs: `aws logs tail /ecs/ytdlp-backend --follow`
2. Verify cookies.txt is not expired (refresh every 2-3 months)
3. Ensure Docker container has `/app/cookies.txt` with proper permissions
4. Try a different YouTube video URL

---

## 🎉 Success Criteria

Your fix is working when:
- ✅ No "Sign in to confirm you're not a bot" errors
- ✅ Videos download successfully
- ✅ Status check shows `ready: true`
- ✅ Downloaded files are accessible via `/video/{file_id}`

Good luck with your deployment! 🚀
