# 🚀 Quick Deployment Commands

Copy and paste these commands to deploy your bot detection fix.

---

## 🔍 Step 1: Verify Changes

```bash
# Check which files changed
git status

# Should show:
# modified:   backend/main.py
# modified:   backend/Dockerfile
# new file:   IMPLEMENTATION_SUMMARY.md
# new file:   TESTING_GUIDE.md
# new file:   BEFORE_AFTER_COMPARISON.md
# new file:   DEPLOYMENT_CHECKLIST_V2.md

# View changes to main.py
git diff backend/main.py

# View changes to Dockerfile
git diff backend/Dockerfile
```

---

## 🧪 Step 2: Test Locally (Recommended)

### Quick Python Test
```bash
# Navigate to backend
cd backend

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Start server
uvicorn main:app --reload

# Open new terminal and test
curl http://localhost:8000/

# Test download (replace with any YouTube URL)
curl -X POST http://localhost:8000/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"}'

# If successful, stop server (Ctrl+C) and proceed to Step 3
```

### Docker Test (Optional but Recommended)
```bash
# Build Docker image
cd backend
docker build -t ytdlp-backend-test:latest .

# Run container
docker run -p 8000:8000 ytdlp-backend-test:latest

# In another terminal, test
curl http://localhost:8000/

# If successful, stop container (Ctrl+C) and proceed
```

---

## 📦 Step 3: Commit Changes

```bash
# Go back to project root
cd ..

# Stage all changes
git add backend/main.py
git add backend/Dockerfile
git add IMPLEMENTATION_SUMMARY.md
git add TESTING_GUIDE.md
git add BEFORE_AFTER_COMPARISON.md
git add DEPLOYMENT_CHECKLIST_V2.md
git add QUICK_DEPLOY_COMMANDS.md

# Commit with descriptive message
git commit -m "Fix: Add cookies and randomized User-Agent to bypass YouTube bot detection

- Added cookies.txt support to authenticate with YouTube
- Implemented randomized User-Agent headers (5 variations)
- Added Accept-Language header for realistic browser behavior
- Increased retry attempts to 5 for better reliability
- Updated Dockerfile to ensure proper cookie file permissions

This resolves the 'Sign in to confirm you're not a bot' error."

# View commit
git log -1 --stat
```

---

## 🔄 Step 4: Deploy to AWS

### Option A: Automated via GitHub Actions (Recommended)

```bash
# Push to GitHub - this will trigger automatic deployment
git push origin main

# Monitor deployment
echo "Monitor deployment at:"
echo "https://github.com/Yudee-19/video-downloader/actions"

# Or use GitHub CLI (if installed)
gh run watch
```

**What happens automatically:**
1. GitHub Actions triggers
2. Backend Docker image builds
3. Image pushes to AWS ECR
4. ECS service updates with new image
5. Old task drains, new task starts

---

### Option B: Manual Deployment

If you don't have GitHub Actions set up or prefer manual deployment:

```bash
# Configure AWS CLI (if not done)
aws configure
# Enter your AWS credentials

# Set variables (REPLACE THESE WITH YOUR VALUES)
export AWS_ACCOUNT_ID="123456789012"
export AWS_REGION="us-east-1"
export ECR_REPO="ytdlp-backend"
export ECS_CLUSTER="ytdlp-cluster"
export ECS_SERVICE="ytdlp-service"

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin \
    ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Build Docker image
cd backend
docker build -t ${ECR_REPO}:latest .

# Tag image
docker tag ${ECR_REPO}:latest \
    ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:latest

# Push to ECR
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:latest

# Update ECS service (force new deployment)
aws ecs update-service \
    --cluster ${ECS_CLUSTER} \
    --service ${ECS_SERVICE} \
    --force-new-deployment \
    --region ${AWS_REGION}

echo "Deployment initiated. Check status with:"
echo "aws ecs describe-services --cluster ${ECS_CLUSTER} --services ${ECS_SERVICE} --region ${AWS_REGION}"
```

---

## 🔍 Step 5: Monitor Deployment

### Check ECS Service Status
```bash
# Check service status
aws ecs describe-services \
    --cluster ytdlp-cluster \
    --services ytdlp-service \
    --region us-east-1 \
    --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,Deployments:deployments[*].{Status:rolloutState,TaskDef:taskDefinition}}'

# Watch task status (run multiple times)
aws ecs list-tasks \
    --cluster ytdlp-cluster \
    --service-name ytdlp-service \
    --region us-east-1

# Check logs in real-time
aws logs tail /ecs/ytdlp-backend --follow --region us-east-1
```

### Check Application Load Balancer
```bash
# Get ALB DNS name (if you forgot it)
aws elbv2 describe-load-balancers \
    --region us-east-1 \
    --query 'LoadBalancers[?contains(LoadBalancerName, `ytdlp`)].DNSName' \
    --output text

# Test ALB health
curl http://YOUR-ALB-DNS-NAME/

# Should return: {"message":"YouTube & Instagram Downloader API","status":"running",...}
```

---

## ✅ Step 6: Verify Deployment

### Test Backend API
```bash
# Set your ALB URL
export ALB_URL="http://ytdlp-alb-123456.us-east-1.elb.amazonaws.com"

# Test health endpoint
curl ${ALB_URL}/

# Test download (with a real YouTube URL)
curl -X POST ${ALB_URL}/download \
    -H "Content-Type: application/json" \
    -d '{"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"}'

# Save the file_id from response
export FILE_ID="<paste-file-id-here>"

# Check status (wait a few seconds, then run)
curl ${ALB_URL}/status/${FILE_ID}

# If ready:true and no error, SUCCESS! ✅
```

### Test Frontend (via browser)
```bash
# Get CloudFront URL
aws cloudfront list-distributions \
    --query 'DistributionList.Items[?contains(Comment, `ytdlp`)].DomainName' \
    --output text

# Or check in AWS Console
# CloudFront → Distributions → Find your distribution → Domain Name
```

1. Open CloudFront URL in browser
2. Paste a YouTube video URL
3. Click "Download"
4. Verify download completes without "bot detection" error

---

## 🎉 Success Indicators

You'll know it worked when:

✅ No errors in CloudWatch logs  
✅ ECS task is running (1/1)  
✅ ALB health check returns 200  
✅ YouTube downloads complete successfully  
✅ No "Sign in to confirm you're not a bot" errors  
✅ Frontend shows successful downloads  

---

## 🐛 Quick Troubleshooting

### Issue: "Still getting bot detection error"

```bash
# Check if cookies.txt is accessible in container
aws ecs list-tasks --cluster ytdlp-cluster --service ytdlp-service --region us-east-1

# Get task ARN, then:
aws ecs execute-command \
    --cluster ytdlp-cluster \
    --task <TASK_ARN> \
    --container ytdlp-backend \
    --command "cat /app/cookies.txt" \
    --interactive \
    --region us-east-1

# Or check Docker image locally:
docker run -it ytdlp-backend:latest ls -la /app/cookies.txt
docker run -it ytdlp-backend:latest cat /app/cookies.txt
```

**Solution:** Cookies might be expired. Export fresh cookies and redeploy.

### Issue: "Container won't start"

```bash
# Check CloudWatch logs
aws logs tail /ecs/ytdlp-backend --follow --region us-east-1

# Check ECS service events
aws ecs describe-services \
    --cluster ytdlp-cluster \
    --services ytdlp-service \
    --region us-east-1 \
    --query 'services[0].events[0:5]'
```

### Issue: "Changes don't seem to take effect"

```bash
# Verify task definition was updated
aws ecs describe-task-definition \
    --task-definition ytdlp-backend \
    --region us-east-1 \
    --query 'taskDefinition.revision'

# Force new deployment (pulls latest image)
aws ecs update-service \
    --cluster ytdlp-cluster \
    --service ytdlp-service \
    --force-new-deployment \
    --region us-east-1

# Wait for deployment to complete
aws ecs wait services-stable \
    --cluster ytdlp-cluster \
    --services ytdlp-service \
    --region us-east-1

echo "Deployment complete!"
```

---

## 🔄 Rollback Commands (If Needed)

```bash
# List recent task definitions
aws ecs list-task-definitions \
    --family-prefix ytdlp-backend \
    --sort DESC \
    --region us-east-1

# Rollback to previous version
aws ecs update-service \
    --cluster ytdlp-cluster \
    --service ytdlp-service \
    --task-definition ytdlp-backend:PREVIOUS_REVISION \
    --region us-east-1

# Or via Git
git revert HEAD
git push origin main
```

---

## 📊 Post-Deployment Monitoring

```bash
# Watch logs continuously
aws logs tail /ecs/ytdlp-backend --follow --region us-east-1

# Check service metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name CPUUtilization \
    --dimensions Name=ServiceName,Value=ytdlp-service Name=ClusterName,Value=ytdlp-cluster \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Average \
    --region us-east-1

# Check ALB target health
aws elbv2 describe-target-health \
    --target-group-arn <YOUR_TARGET_GROUP_ARN> \
    --region us-east-1
```

---

## 📝 What's Next?

After successful deployment:

1. **Monitor for 24 hours** - Watch CloudWatch logs
2. **Test various videos** - Try different YouTube URLs
3. **Set cookie refresh reminder** - Cookies expire every 2-3 months
4. **Update documentation** - Note deployment date and version
5. **Gather user feedback** - Ensure downloads work as expected

---

## 📞 Need Help?

If deployment fails:

1. Check CloudWatch logs first
2. Verify cookies.txt is not expired
3. Review this checklist
4. Check AWS service status
5. Review DEPLOYMENT_CHECKLIST_V2.md for detailed troubleshooting

---

## 🎯 Quick Reference

| Command | Purpose |
|---------|---------|
| `git push origin main` | Deploy via GitHub Actions |
| `aws ecs update-service --force-new-deployment` | Manual deploy |
| `aws logs tail /ecs/ytdlp-backend --follow` | View logs |
| `curl http://ALB_URL/` | Test backend |
| `aws ecs describe-services` | Check service status |

---

**Ready to deploy? Start with Step 1! 🚀**
