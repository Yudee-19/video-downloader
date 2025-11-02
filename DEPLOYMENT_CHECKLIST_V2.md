# ✅ Deployment Checklist - Bot Detection Fix

Use this checklist to ensure your bot detection fix is properly deployed to AWS.

---

## 📋 Pre-Deployment Checklist

### 1. Local Code Verification
- [ ] `backend/main.py` includes `import random`
- [ ] `USER_AGENTS` list is defined with 5+ user agent strings
- [ ] `COOKIES_FILE` variable is defined
- [ ] `base_opts` includes `cookiefile` parameter
- [ ] `base_opts` includes `http_headers` with User-Agent and Accept-Language
- [ ] `retries` and `fragment_retries` are set to 5

### 2. Docker Configuration
- [ ] `backend/Dockerfile` includes `chmod 644 /app/cookies.txt`
- [ ] `backend/cookies.txt` file exists
- [ ] `backend/cookies.txt` has valid YouTube session cookies
- [ ] Cookies are not expired (check expiration timestamps in file)

### 3. Git Repository
- [ ] All changes are committed locally
- [ ] `.gitignore` allows `cookies.txt` (or consider security implications)
- [ ] Changes are ready to push to GitHub

---

## 🧪 Testing Phase

### Local Python Testing
```bash
cd backend
uvicorn main:app --reload
```

- [ ] Server starts without errors
- [ ] `http://localhost:8000/` returns API info
- [ ] Can download a test video without bot errors
- [ ] Check logs for User-Agent randomization

**Test Command:**
```bash
curl -X POST http://localhost:8000/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"}'
```

### Local Docker Testing
```bash
cd backend
docker build -t ytdlp-backend-test:latest .
docker run -p 8000:8000 ytdlp-backend-test:latest
```

- [ ] Docker build completes successfully
- [ ] Container starts without errors
- [ ] `docker exec` shows cookies.txt exists at `/app/cookies.txt`
- [ ] Can download a test video from containerized app

**Verification Commands:**
```bash
# Check cookies file in container
docker ps  # Get container ID
docker exec -it <CONTAINER_ID> ls -la /app/cookies.txt
docker exec -it <CONTAINER_ID> head -5 /app/cookies.txt
```

---

## 🚀 Deployment Phase

### Option A: Automated Deployment (GitHub Actions)

#### Commit and Push
```bash
git add backend/main.py backend/Dockerfile
git add IMPLEMENTATION_SUMMARY.md TESTING_GUIDE.md BEFORE_AFTER_COMPARISON.md
git commit -m "Fix: Add cookies and randomized User-Agent to bypass YouTube bot detection"
git push origin main
```

- [ ] Code pushed to GitHub
- [ ] GitHub Actions workflow triggered
- [ ] Backend workflow completes successfully
- [ ] New Docker image pushed to ECR
- [ ] ECS service updated

**Monitor:**
- GitHub Actions: `https://github.com/YOUR_USERNAME/ytdlp-demo/actions`

---

### Option B: Manual Deployment

#### Build and Push to ECR
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build image
cd backend
docker build -t ytdlp-backend:latest .

# Tag image
docker tag ytdlp-backend:latest \
    YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ytdlp-backend:latest

# Push to ECR
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ytdlp-backend:latest
```

- [ ] Successfully logged into ECR
- [ ] Docker image built without errors
- [ ] Image tagged correctly
- [ ] Image pushed to ECR successfully

#### Update ECS Service
```bash
# Force new deployment
aws ecs update-service \
    --cluster ytdlp-cluster \
    --service ytdlp-service \
    --force-new-deployment \
    --region us-east-1
```

- [ ] ECS service update command executed
- [ ] New task is starting
- [ ] Old task is draining
- [ ] New task is running

---

## 🔍 Post-Deployment Verification

### AWS Console Checks

#### ECS Service Status
1. Go to AWS Console → ECS → Clusters → `ytdlp-cluster`
2. Click on `ytdlp-service`
3. Check:
   - [ ] Desired tasks: 1
   - [ ] Running tasks: 1
   - [ ] Task definition: Latest revision
   - [ ] Last deployment status: PRIMARY

#### CloudWatch Logs
1. Go to AWS Console → CloudWatch → Log groups
2. Find `/ecs/ytdlp-backend`
3. Check recent logs:
   - [ ] No error messages on startup
   - [ ] Application started successfully
   - [ ] No "cookiefile not found" errors

**CLI Alternative:**
```bash
aws logs tail /ecs/ytdlp-backend --follow --region us-east-1
```

### Functional Testing

#### Test ALB Health
```bash
curl http://YOUR-ALB-URL.us-east-1.elb.amazonaws.com/
```

- [ ] Returns API information
- [ ] Status code: 200 OK
- [ ] Response includes "YouTube & Instagram Downloader API"

#### Test Video Download
```bash
curl -X POST http://YOUR-ALB-URL.us-east-1.elb.amazonaws.com/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"}'

# Save the file_id from response, then check status:
curl http://YOUR-ALB-URL.us-east-1.elb.amazonaws.com/status/<FILE_ID>
```

- [ ] Download endpoint returns `file_id`
- [ ] Status endpoint shows `ready: true` after waiting
- [ ] No error messages about bot detection
- [ ] Video file is downloadable

#### Test via Frontend
1. Open your CloudFront URL
2. Paste a YouTube URL
3. Click Download
4. Wait for completion

- [ ] Frontend loads successfully
- [ ] Can paste YouTube URL
- [ ] Download starts
- [ ] Progress shows
- [ ] Download completes without errors
- [ ] File can be downloaded

---

## 🎯 Success Criteria

All of the following must be ✅:

### Core Functionality
- [ ] Backend API is accessible
- [ ] Can download YouTube videos
- [ ] Can download Instagram videos
- [ ] No "Sign in to confirm you're not a bot" errors
- [ ] Downloaded files are accessible

### Technical Requirements
- [ ] ECS service is running
- [ ] CloudWatch logs show no errors
- [ ] ALB health checks passing
- [ ] Cookies.txt is accessible in container
- [ ] User-Agent randomization is working

### User Experience
- [ ] Frontend loads successfully
- [ ] Downloads complete successfully
- [ ] No error messages to users
- [ ] Download speeds are acceptable

---

## 🐛 Troubleshooting Guide

### Issue: Still getting bot detection errors

**Checklist:**
- [ ] Verify cookies.txt is not expired
- [ ] Check cookies.txt exists in container: `docker exec <id> cat /app/cookies.txt`
- [ ] Confirm cookies are from a logged-in YouTube session
- [ ] Try exporting fresh cookies from browser

**Solution:**
1. Export new cookies from browser
2. Replace `backend/cookies.txt`
3. Redeploy

### Issue: Container fails to start

**Checklist:**
- [ ] Check CloudWatch logs for errors
- [ ] Verify Dockerfile syntax is correct
- [ ] Ensure cookies.txt exists in backend folder
- [ ] Check ECS task definition is correct

**Debug Commands:**
```bash
# Check ECS service events
aws ecs describe-services \
    --cluster ytdlp-cluster \
    --services ytdlp-service \
    --region us-east-1

# View task logs
aws logs tail /ecs/ytdlp-backend --follow --region us-east-1
```

### Issue: "cookiefile not found" error

**Checklist:**
- [ ] Verify `COPY . .` in Dockerfile includes cookies.txt
- [ ] Check cookies.txt is not in `.dockerignore`
- [ ] Confirm file permissions: `chmod 644 cookies.txt`

**Solution:**
```bash
# In backend directory
ls -la cookies.txt  # Should show the file
cat .dockerignore   # Make sure cookies.txt is not excluded
```

### Issue: Downloads are slow or timing out

**Checklist:**
- [ ] Check network connectivity from ECS
- [ ] Verify EFS is mounted correctly (if using)
- [ ] Check ALB timeout settings
- [ ] Monitor CloudWatch metrics

**Solution:**
- Increase retries in yt-dlp options
- Add `http_chunk_size` option
- Check AWS network ACLs and security groups

---

## 📊 Monitoring & Maintenance

### Daily
- [ ] Check CloudWatch for error logs
- [ ] Monitor download success rate

### Weekly
- [ ] Review download patterns
- [ ] Check storage usage (EFS/EBS)
- [ ] Clean up old temporary files

### Monthly
- [ ] Test downloads are still working
- [ ] Review AWS costs
- [ ] Update dependencies if needed

### Every 2-3 Months
- [ ] **Export fresh YouTube cookies**
- [ ] Update `backend/cookies.txt`
- [ ] Redeploy application

---

## 📝 Rollback Plan

If deployment fails or causes issues:

### Quick Rollback via ECS
```bash
# Get previous task definition
aws ecs describe-task-definition \
    --task-definition ytdlp-backend \
    --region us-east-1

# Update service to previous revision
aws ecs update-service \
    --cluster ytdlp-cluster \
    --service ytdlp-service \
    --task-definition ytdlp-backend:PREVIOUS_REVISION \
    --region us-east-1
```

### Rollback via Git
```bash
# Revert commit
git revert HEAD
git push origin main

# GitHub Actions will auto-deploy reverted version
```

---

## ✨ Final Validation

Once everything is checked:

- [ ] YouTube downloads work without bot errors ✅
- [ ] Instagram downloads still work ✅
- [ ] Frontend is functional ✅
- [ ] No errors in CloudWatch logs ✅
- [ ] Application performance is acceptable ✅
- [ ] Users can successfully download videos ✅

---

## 🎉 Deployment Complete!

If all items are checked, your bot detection fix is successfully deployed.

### Next Steps:
1. Monitor for 24-48 hours
2. Collect user feedback
3. Set up cookie refresh reminder (2-3 months)
4. Document any additional issues

### Support:
- CloudWatch Logs: `/ecs/ytdlp-backend`
- GitHub Issues: Create issue if problems persist
- AWS Support: Contact if infrastructure issues

---

**Deployment Date:** ________________  
**Deployed By:** ________________  
**Git Commit:** ________________  
**Status:** ☐ Success  ☐ Failed  ☐ Needs Review

---

## 📚 Reference Documents

- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - Detailed changes
- [TESTING_GUIDE.md](./TESTING_GUIDE.md) - Testing procedures
- [BEFORE_AFTER_COMPARISON.md](./BEFORE_AFTER_COMPARISON.md) - Visual comparison
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Full AWS deployment guide
- [v2.md](./v2.md) - Original fix documentation
