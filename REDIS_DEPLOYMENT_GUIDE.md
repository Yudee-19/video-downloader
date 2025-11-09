# 🚀 Redis-Enabled Multiple Downloads Deployment Guide

## Complete Guide for Deploying YouTube Downloader with Batch Downloads

This guide walks you through deploying the enhanced version with **Redis**, **parallel downloads**, and **batch download support**.

---

## 📋 Table of Contents

1. [What's New](#whats-new)
2. [Architecture Overview](#architecture-overview)
3. [Prerequisites](#prerequisites)
4. [Local Testing with Redis](#local-testing-with-redis)
5. [AWS Deployment](#aws-deployment)
6. [Configuration](#configuration)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)
9. [Cost Estimate](#cost-estimate)

---

## 🆕 What's New

### New Features:
- ✅ **Batch Downloads**: Download multiple videos simultaneously
- ✅ **Redis Integration**: Persistent state across container restarts
- ✅ **Parallel Processing**: Up to 3 concurrent downloads (configurable)
- ✅ **Real-time Progress**: Individual progress tracking for each video
- ✅ **Better Scalability**: Can scale ECS tasks without losing state
- ✅ **Queue Management**: Smart queuing system for downloads

### New Components:
- **ElastiCache Redis**: For persistent download state
- **BatchDownloadForm**: Frontend component for batch downloads
- **BatchDownloadStatus**: Real-time batch progress tracker
- **Thread Pool Executor**: Backend parallel processing

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                        Users                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   CloudFront (CDN)    │  ← Frontend (React)
         │  + S3 Static Hosting  │
         └───────────┬───────────┘
                     │
                     │ API Calls
                     ▼
         ┌───────────────────────┐
         │  Application Load     │
         │     Balancer (ALB)    │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   ECS Fargate         │  ← Backend (FastAPI)
         │   (Docker Container)  │     + Thread Pool
         │   + Auto Scaling      │
         └─────┬─────────┬───────┘
               │         │
               │         └─────────────┐
               ▼                       ▼
    ┌──────────────────┐    ┌──────────────────┐
    │  ElastiCache     │    │   EFS (Elastic   │
    │  Redis Cluster   │    │   File System)   │
    │  (State Store)   │    │   (Video Files)  │
    └──────────────────┘    └──────────────────┘
```

---

## ✅ Prerequisites

### 1. AWS Account Setup
- AWS account with admin access
- AWS CLI installed and configured
- Billing alerts enabled

### 2. Local Tools
```bash
# Install AWS CLI (if not installed)
pip install awscli

# Configure AWS CLI
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1), Output (json)

# Verify AWS connection
aws sts get-caller-identity
```

### 3. Docker Desktop
- Download: https://www.docker.com/products/docker-desktop
- Ensure Docker is running

### 4. GitHub Repository
```bash
# Push your updated code
git add .
git commit -m "Add Redis and batch download support"
git push origin main
```

---

## 🧪 Local Testing with Redis

### Step 1: Install Redis Locally

**Windows:**
```bash
# Using WSL2 (recommended)
wsl --install
wsl
sudo apt update
sudo apt install redis-server
redis-server
```

**Mac:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
```

### Step 2: Test Backend Locally

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export REDIS_HOST=localhost
export REDIS_PORT=6379
export MAX_PARALLEL_DOWNLOADS=3

# Run backend
python main.py
```

### Step 3: Test Frontend Locally

```bash
cd frontend

# Install dependencies
npm install

# Create .env.development
echo "REACT_APP_API_URL=http://localhost:8000" > .env.development

# Run frontend
npm start
```

### Step 4: Test Batch Downloads

1. Open http://localhost:3000
2. Click "Batch Download"
3. Add 3-5 YouTube URLs
4. Click "Download All"
5. Watch real-time progress for each video

---

## 🚀 AWS Deployment

### Step 1: Deploy Infrastructure with Redis

```bash
# Deploy CloudFormation stack (includes Redis)
aws cloudformation create-stack \
    --stack-name ytdlp-infrastructure \
    --template-body file://aws/cloudformation-template.yaml \
    --capabilities CAPABILITY_IAM \
    --region us-east-1

# Wait for completion (10-15 minutes)
aws cloudformation wait stack-create-complete \
    --stack-name ytdlp-infrastructure \
    --region us-east-1
```

### Step 2: Get Stack Outputs

```bash
# Get all outputs
aws cloudformation describe-stacks \
    --stack-name ytdlp-infrastructure \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table
```

**Save these values:**
- `RedisEndpoint` - **IMPORTANT!**
- `RedisPort` - Usually 6379
- `ECRRepositoryURI`
- `ECSClusterName`
- `ALBDNSName`
- `CloudFrontDomain`
- `CloudFrontDistributionId`
- `S3BucketName`
- `EFSFileSystemId`
- `ECSSecurityGroupId`
- `PublicSubnet1Id`
- `PublicSubnet2Id`
- `ALBTargetGroupArn`

### Step 3: Update ECS Task Definition

```bash
# Get your AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Get Redis endpoint from CloudFormation
REDIS_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name ytdlp-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`RedisEndpoint`].OutputValue' \
    --output text)

echo "Redis Endpoint: $REDIS_ENDPOINT"

# Update task definition (for Windows use text editor)
# Replace YOUR_REDIS_ENDPOINT in aws/ecs-task-definition.json with actual Redis endpoint
```

**Manually edit `aws/ecs-task-definition.json`:**
- Replace `YOUR_ACCOUNT_ID` with your AWS Account ID
- Replace `YOUR_REDIS_ENDPOINT` with the Redis endpoint from CloudFormation
- Replace `YOUR_EFS_ID` with EFS ID from outputs
- Replace `YOUR_CLOUDFRONT_DOMAIN` with CloudFront domain

### Step 4: Build and Push Backend Docker Image

```bash
cd backend

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build Docker image
docker build -t ytdlp-backend:latest .

# Tag image
docker tag ytdlp-backend:latest \
    $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ytdlp-backend:latest

# Push to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ytdlp-backend:latest
```

### Step 5: Register ECS Task Definition

```bash
# Register task definition
aws ecs register-task-definition \
    --cli-input-json file://aws/ecs-task-definition.json \
    --region us-east-1
```

### Step 6: Create ECS Service

```bash
# Get subnet and security group IDs from CloudFormation outputs
SUBNET1=$(aws cloudformation describe-stacks \
    --stack-name ytdlp-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`PublicSubnet1Id`].OutputValue' \
    --output text)

SUBNET2=$(aws cloudformation describe-stacks \
    --stack-name ytdlp-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`PublicSubnet2Id`].OutputValue' \
    --output text)

ECS_SG=$(aws cloudformation describe-stacks \
    --stack-name ytdlp-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`ECSSecurityGroupId`].OutputValue' \
    --output text)

TG_ARN=$(aws cloudformation describe-stacks \
    --stack-name ytdlp-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`ALBTargetGroupArn`].OutputValue' \
    --output text)

# Create ECS service
aws ecs create-service \
    --cluster ytdlp-cluster \
    --service-name ytdlp-service \
    --task-definition ytdlp-backend \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET1,$SUBNET2],securityGroups=[$ECS_SG],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=$TG_ARN,containerName=ytdlp-backend,containerPort=8000" \
    --region us-east-1
```

### Step 7: Wait for Service to Start

```bash
# Check service status
aws ecs describe-services \
    --cluster ytdlp-cluster \
    --services ytdlp-service \
    --region us-east-1

# Check logs
aws logs tail /ecs/ytdlp-backend --follow --region us-east-1
```

### Step 8: Deploy Frontend

```bash
cd ../frontend

# Get ALB DNS
ALB_DNS=$(aws cloudformation describe-stacks \
    --stack-name ytdlp-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`ALBDNSName`].OutputValue' \
    --output text)

# Create production env file
echo "REACT_APP_API_URL=http://$ALB_DNS" > .env.production

# Build frontend
npm install
npm run build

# Get S3 bucket name
S3_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name ytdlp-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' \
    --output text)

# Deploy to S3
aws s3 sync build/ s3://$S3_BUCKET/ --delete

# Get CloudFront distribution ID
CF_DIST_ID=$(aws cloudformation describe-stacks \
    --stack-name ytdlp-infrastructure \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
    --output text)

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
    --distribution-id $CF_DIST_ID \
    --paths "/*"
```

---

## ⚙️ Configuration

### Backend Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REDIS_HOST` | Redis endpoint | localhost | Yes |
| `REDIS_PORT` | Redis port | 6379 | Yes |
| `REDIS_PASSWORD` | Redis password | None | No |
| `MAX_PARALLEL_DOWNLOADS` | Max concurrent downloads | 3 | No |
| `CORS_ORIGINS` | Allowed origins | * | Yes |
| `TEMP_DIR` | Video storage | /mnt/efs/tmp_videos | Yes |

### Adjusting Parallel Downloads

To increase parallel downloads, update:

1. **ECS Task Definition** (`aws/ecs-task-definition.json`):
```json
{
  "name": "MAX_PARALLEL_DOWNLOADS",
  "value": "5"
}
```

2. **Increase CPU/Memory** if needed:
```json
{
  "cpu": "2048",
  "memory": "4096"
}
```

---

## 🧪 Testing

### Test 1: Single Download
1. Go to CloudFront URL
2. Paste YouTube URL
3. Click "Download"
4. Verify download works

### Test 2: Batch Download
1. Click "Batch Download" tab
2. Add 5 different YouTube URLs
3. Click "Download All (5 videos)"
4. Watch real-time progress
5. Verify all downloads complete

### Test 3: Parallel Downloads
1. Start batch download with 5 videos
2. Check logs to verify 3 download simultaneously:
```bash
aws logs tail /ecs/ytdlp-backend --follow
```

### Test 4: Redis Persistence
1. Start a batch download
2. Scale ECS service to 0:
```bash
aws ecs update-service --cluster ytdlp-cluster --service ytdlp-service --desired-count 0
```
3. Scale back to 1:
```bash
aws ecs update-service --cluster ytdlp-cluster --service ytdlp-service --desired-count 1
```
4. Check if download state persists (Note: downloads will restart)

---

## 🐛 Troubleshooting

### Redis Connection Failed

**Symptom**: Logs show "Redis connection failed"

**Solution**:
```bash
# Check Redis cluster status
aws elasticache describe-cache-clusters \
    --show-cache-node-info \
    --region us-east-1

# Verify security group allows port 6379
aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=ytdlp-redis-sg" \
    --region us-east-1
```

### Backend Not Starting

**Check logs**:
```bash
aws logs tail /ecs/ytdlp-backend --follow
```

**Common issues**:
- Wrong Redis endpoint
- Security group blocking Redis port
- Insufficient CPU/memory

### Batch Downloads Not Working

**Test API directly**:
```bash
# Test single download endpoint
curl -X POST http://YOUR-ALB-DNS/download \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Test batch download endpoint
curl -X POST http://YOUR-ALB-DNS/batch-download \
  -H "Content-Type: application/json" \
  -d '{"urls":["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]}'
```

### High Memory Usage

**Reduce parallel downloads**:
```bash
# Update service with new task definition
# First, edit MAX_PARALLEL_DOWNLOADS to 2 in task definition
# Then:
aws ecs register-task-definition --cli-input-json file://aws/ecs-task-definition.json
aws ecs update-service --cluster ytdlp-cluster --service ytdlp-service --force-new-deployment
```

---

## 💰 Cost Estimate

### Monthly Costs (Updated)

| Service | Configuration | Cost |
|---------|---------------|------|
| **ECS Fargate** | 1 task, 1 vCPU, 2 GB RAM | ~$30 |
| **ElastiCache Redis** | cache.t3.micro | ~$12 |
| **Application Load Balancer** | 1 ALB | ~$16 |
| **EFS** | 20 GB storage | ~$6 |
| **S3** | 5 GB | ~$0.50 |
| **CloudFront** | 100 GB transfer | ~$8.50 |
| **ECR** | 1 GB | ~$0.10 |
| **Data Transfer** | Varies | ~$10 |
| **Total** | | **~$83/month** |

### Cost Optimization Tips:
1. **Use Redis snapshot**: Enable for persistence across node replacement
2. **ECS Auto-scaling**: Scale to 0 during off-hours
3. **Spot pricing**: Consider Fargate Spot (70% discount)
4. **Reserved instances**: For production workloads

---

## 📊 Monitoring

### CloudWatch Dashboards

```bash
# Create custom dashboard
aws cloudwatch put-dashboard \
  --dashboard-name ytdlp-monitoring \
  --dashboard-body file://monitoring-dashboard.json
```

### Key Metrics to Monitor:
- ECS CPU/Memory utilization
- Redis connections
- ALB request count
- EFS throughput
- Active downloads count

---

## 🔄 CI/CD Setup

### GitHub Secrets

Add these to GitHub → Settings → Secrets:

| Secret | Value |
|--------|-------|
| `AWS_ACCESS_KEY_ID` | Your AWS key |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret |
| `AWS_REGION` | us-east-1 |
| `ECR_REPOSITORY` | ytdlp-backend |
| `ECS_CLUSTER` | ytdlp-cluster |
| `ECS_SERVICE` | ytdlp-service |
| `S3_BUCKET` | Your S3 bucket |
| `CLOUDFRONT_DISTRIBUTION_ID` | Your CF ID |
| `API_URL` | http://your-alb-dns |

The existing GitHub Actions workflows will automatically deploy changes.

---

## 🎯 Success Checklist

- [ ] CloudFormation stack created successfully
- [ ] Redis cluster accessible from ECS
- [ ] Backend container running
- [ ] Frontend accessible via CloudFront
- [ ] Single download works
- [ ] Batch download works
- [ ] Parallel downloads confirmed (check logs)
- [ ] Redis persistence verified
- [ ] GitHub Actions deploying successfully
- [ ] CloudWatch logs visible
- [ ] Cost alerts configured

---

## 🚀 What's Next?

1. **Add Authentication**: Implement user accounts
2. **Rate Limiting**: Prevent abuse
3. **Download History**: Store completed downloads
4. **WebSocket Support**: Real-time progress updates
5. **S3 Storage**: Move videos to S3 instead of EFS
6. **CDN for Videos**: Serve videos via CloudFront
7. **Custom Domain**: Add your own domain

---

## 📞 Support

**Need help?**
- Check CloudWatch logs: `/ecs/ytdlp-backend`
- Review ECS service events
- Verify security group rules
- Test Redis connectivity

**Common Commands:**
```bash
# View logs
aws logs tail /ecs/ytdlp-backend --follow

# Force new deployment
aws ecs update-service --cluster ytdlp-cluster --service ytdlp-service --force-new-deployment

# Scale service
aws ecs update-service --cluster ytdlp-cluster --service ytdlp-service --desired-count 2

# Check Redis
redis-cli -h YOUR-REDIS-ENDPOINT ping
```

---

**🎉 Congratulations!** You now have a production-ready YouTube downloader with batch download support!
