# 🚀 AWS Deployment Guide with CI/CD Pipeline

This guide will walk you through deploying your YouTube & Instagram Downloader application to AWS with automated CI/CD using GitHub Actions.

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [AWS Services Setup](#aws-services-setup)
4. [Backend Deployment (ECS/Fargate)](#backend-deployment)
5. [Frontend Deployment (S3 + CloudFront)](#frontend-deployment)
6. [CI/CD Pipeline Setup](#cicd-pipeline-setup)
7. [Environment Configuration](#environment-configuration)
8. [Cost Estimation](#cost-estimation)
9. [Troubleshooting](#troubleshooting)

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
         │   (Docker Container)  │
         │   + Auto Scaling      │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   EFS (Elastic File   │  ← Temporary video storage
         │      System)          │
         └───────────────────────┘
```

### Services Used:
- **Frontend**: S3 (storage) + CloudFront (CDN)
- **Backend**: ECS Fargate (containerized FastAPI)
- **Load Balancer**: Application Load Balancer (ALB)
- **Storage**: EFS for temporary video files
- **Registry**: ECR (Elastic Container Registry) for Docker images
- **CI/CD**: GitHub Actions
- **Secrets**: AWS Secrets Manager
- **Monitoring**: CloudWatch

---

## ✅ Prerequisites

### 1. AWS Account
- [ ] Create AWS account: https://aws.amazon.com/
- [ ] Set up billing alerts
- [ ] Enable MFA for root account

### 2. Local Tools
```bash
# Install AWS CLI
# Windows (using pip)
pip install awscli

# Configure AWS CLI
aws configure
# Enter: Access Key ID, Secret Access Key, Region (e.g., us-east-1), Output format (json)
```

### 3. GitHub Repository
```bash
# Initialize git if not done
git init
git add .
git commit -m "Initial commit"

# Create GitHub repository and push
git remote add origin https://github.com/YOUR_USERNAME/ytdlp-demo.git
git branch -M main
git push -u origin main
```

### 4. Install Docker Desktop
- Download: https://www.docker.com/products/docker-desktop
- Required for local testing

---

## 🔧 AWS Services Setup

### Step 1: Create IAM User for Deployment

1. **Go to IAM Console** → Users → Add User
   - Username: `github-actions-deployer`
   - Access type: Programmatic access

2. **Attach Policies**:
   - `AmazonEC2ContainerRegistryFullAccess`
   - `AmazonECS_FullAccess`
   - `AmazonS3FullAccess`
   - `CloudFrontFullAccess`
   - `AmazonElasticFileSystemFullAccess`
   - `IAMFullAccess` (for creating roles)

3. **Save Credentials**:
   - Save Access Key ID
   - Save Secret Access Key
   - You'll add these to GitHub Secrets

### Step 2: Create ECR Repositories

```bash
# Create repository for backend
aws ecr create-repository \
    --repository-name ytdlp-backend \
    --region us-east-1

# Note the repositoryUri from output
# Example: 123456789012.dkr.ecr.us-east-1.amazonaws.com/ytdlp-backend
```

### Step 3: Create EFS File System

1. **Go to EFS Console** → Create file system
   - Name: `ytdlp-video-storage`
   - VPC: Default VPC
   - Availability zones: Select all in your region
   - Performance mode: General Purpose
   - Throughput mode: Bursting

2. **Note the File System ID** (e.g., `fs-12345678`)

### Step 4: Create VPC and Security Groups

```bash
# Create security group for ECS tasks
aws ec2 create-security-group \
    --group-name ytdlp-ecs-sg \
    --description "Security group for YT-DLP ECS tasks" \
    --vpc-id vpc-XXXXX

# Allow HTTP traffic (port 8000)
aws ec2 authorize-security-group-ingress \
    --group-id sg-XXXXX \
    --protocol tcp \
    --port 8000 \
    --cidr 0.0.0.0/0

# Allow EFS traffic (port 2049) from ECS security group
aws ec2 authorize-security-group-ingress \
    --group-id <EFS-SG-ID> \
    --protocol tcp \
    --port 2049 \
    --source-group <ECS-SG-ID>
```

### Step 5: Create Application Load Balancer

1. **Go to EC2 Console** → Load Balancers → Create Load Balancer
2. **Select Application Load Balancer**
3. **Configure**:
   - Name: `ytdlp-alb`
   - Scheme: Internet-facing
   - IP address type: IPv4
   - Listeners: HTTP (80), HTTPS (443) - optional
   - Availability Zones: Select at least 2

4. **Create Target Group**:
   - Name: `ytdlp-backend-tg`
   - Target type: IP
   - Protocol: HTTP
   - Port: 8000
   - Health check path: `/`

5. **Note the ALB DNS name** (e.g., `ytdlp-alb-123456789.us-east-1.elb.amazonaws.com`)

---

## 🐳 Backend Deployment

### Step 1: Create ECS Cluster

```bash
# Create ECS cluster
aws ecs create-cluster \
    --cluster-name ytdlp-cluster \
    --region us-east-1
```

### Step 2: Create Task Execution Role

```bash
# Create trust policy file
cat > ecs-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create IAM role
aws iam create-role \
    --role-name ecsTaskExecutionRole \
    --assume-role-policy-document file://ecs-trust-policy.json

# Attach policies
aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonElasticFileSystemFullAccess
```

### Step 3: Test Backend Docker Image Locally

```bash
cd backend

# Build Docker image
docker build -t ytdlp-backend:latest .

# Run locally to test
docker run -p 8000:8000 ytdlp-backend:latest

# Test API
curl http://localhost:8000/
```

### Step 4: Push to ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    123456789012.dkr.ecr.us-east-1.amazonaws.com

# Tag image
docker tag ytdlp-backend:latest \
    123456789012.dkr.ecr.us-east-1.amazonaws.com/ytdlp-backend:latest

# Push image
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/ytdlp-backend:latest
```

### Step 5: Create ECS Service

The service will be created via the task definition and GitHub Actions. The task definition file is in `aws/ecs-task-definition.json`.

---

## 🌐 Frontend Deployment

### Step 1: Create S3 Bucket

```bash
# Create bucket (must be globally unique)
aws s3 mb s3://ytdlp-frontend-YOUR-NAME --region us-east-1

# Enable static website hosting
aws s3 website s3://ytdlp-frontend-YOUR-NAME \
    --index-document index.html \
    --error-document index.html

# Set bucket policy for public read
cat > bucket-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::ytdlp-frontend-YOUR-NAME/*"
    }
  ]
}
EOF

aws s3api put-bucket-policy \
    --bucket ytdlp-frontend-YOUR-NAME \
    --policy file://bucket-policy.json
```

### Step 2: Create CloudFront Distribution

1. **Go to CloudFront Console** → Create Distribution
2. **Configure**:
   - Origin domain: `ytdlp-frontend-YOUR-NAME.s3-website-us-east-1.amazonaws.com`
   - Origin protocol: HTTP only
   - Viewer protocol policy: Redirect HTTP to HTTPS
   - Allowed HTTP methods: GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE
   - Cache policy: CachingOptimized
   - Default root object: `index.html`

3. **Create Custom Error Responses**:
   - HTTP Error Code: 403 → Response Page Path: `/index.html` → HTTP Response Code: 200
   - HTTP Error Code: 404 → Response Page Path: `/index.html` → HTTP Response Code: 200

4. **Note CloudFront Domain Name** (e.g., `d123456789.cloudfront.net`)

### Step 3: Update Frontend API URL

The API URL will be set via environment variables during build. See `frontend/.env.production` file.

---

## ⚙️ CI/CD Pipeline Setup

### Step 1: Add GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AWS_ACCESS_KEY_ID` | Your AWS Access Key | From IAM user |
| `AWS_SECRET_ACCESS_KEY` | Your AWS Secret Key | From IAM user |
| `AWS_REGION` | `us-east-1` | Your AWS region |
| `ECR_REPOSITORY` | `ytdlp-backend` | ECR repo name |
| `ECS_CLUSTER` | `ytdlp-cluster` | ECS cluster name |
| `ECS_SERVICE` | `ytdlp-service` | ECS service name |
| `S3_BUCKET` | `ytdlp-frontend-YOUR-NAME` | S3 bucket name |
| `CLOUDFRONT_DISTRIBUTION_ID` | `E1234567890ABC` | From CloudFront |
| `API_URL` | `http://ytdlp-alb-123.us-east-1.elb.amazonaws.com` | ALB URL |

### Step 2: GitHub Actions Workflows

Two workflow files are created:
1. `.github/workflows/deploy-backend.yml` - Deploys backend to ECS
2. `.github/workflows/deploy-frontend.yml` - Deploys frontend to S3/CloudFront

These workflows will:
- Trigger on push to `main` branch
- Build Docker images (backend)
- Build React app (frontend)
- Deploy to AWS
- Invalidate CloudFront cache

### Step 3: Test the Pipeline

```bash
# Make a small change
echo "# Test deployment" >> README.md

# Commit and push
git add .
git commit -m "Test CI/CD pipeline"
git push origin main

# Watch GitHub Actions
# Go to: https://github.com/YOUR_USERNAME/ytdlp-demo/actions
```

---

## 🔐 Environment Configuration

### Backend Environment Variables

Set in ECS Task Definition:
```json
{
  "environment": [
    {
      "name": "CORS_ORIGINS",
      "value": "https://d123456789.cloudfront.net,https://yourdomain.com"
    },
    {
      "name": "TEMP_DIR",
      "value": "/mnt/efs/tmp_videos"
    },
    {
      "name": "ENVIRONMENT",
      "value": "production"
    }
  ]
}
```

### Frontend Environment Variables

Create `.env.production` in frontend/:
```bash
REACT_APP_API_URL=http://ytdlp-alb-123456789.us-east-1.elb.amazonaws.com
```

---

## 💰 Cost Estimation

### Monthly Costs (Approximate)

| Service | Usage | Cost |
|---------|-------|------|
| **ECS Fargate** | 1 task, 0.5 vCPU, 1 GB RAM | ~$15-20 |
| **Application Load Balancer** | 1 ALB | ~$16 |
| **EFS** | 20 GB storage + data transfer | ~$6-10 |
| **S3** | 5 GB storage, 10K requests | ~$0.50 |
| **CloudFront** | 100 GB data transfer | ~$8.50 |
| **ECR** | 1 GB storage | ~$0.10 |
| **Data Transfer** | Varies | ~$5-15 |
| **Total** | | **~$51-75/month** |

### Cost Optimization Tips:
- Use ECS Task auto-scaling (scale to 0 when not in use)
- Enable EFS Infrequent Access
- Set S3 lifecycle policies
- Use CloudFront caching effectively
- Delete old ECR images

---

## 🐛 Troubleshooting

### Backend Issues

#### Service won't start
```bash
# Check ECS service events
aws ecs describe-services \
    --cluster ytdlp-cluster \
    --services ytdlp-service

# Check task logs
aws logs tail /ecs/ytdlp-backend --follow
```

#### EFS mount fails
- Verify ECS task security group allows port 2049
- Check EFS mount targets are in same VPC/subnets
- Verify EFS security group allows inbound from ECS SG

#### Container health check failing
- Verify container is listening on port 8000
- Check `/` endpoint returns 200 OK
- Review CloudWatch logs

### Frontend Issues

#### Build fails in GitHub Actions
- Check `REACT_APP_API_URL` is set correctly
- Verify Node.js version compatibility
- Check for TypeScript errors

#### CloudFront shows old content
```bash
# Invalidate CloudFront cache
aws cloudfront create-invalidation \
    --distribution-id E1234567890ABC \
    --paths "/*"
```

#### CORS errors
- Update backend CORS origins to include CloudFront domain
- Verify ALB is allowing traffic from CloudFront
- Check browser console for specific error

### CI/CD Issues

#### GitHub Actions failing
- Verify all secrets are set correctly
- Check AWS credentials haven't expired
- Review action logs for specific errors

#### ECR push fails
```bash
# Re-authenticate
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    123456789012.dkr.ecr.us-east-1.amazonaws.com
```

---

## 🎯 Deployment Checklist

### Before First Deployment

- [ ] AWS account created and configured
- [ ] IAM user created with proper permissions
- [ ] ECR repository created
- [ ] ECS cluster created
- [ ] EFS file system created
- [ ] Security groups configured
- [ ] Load balancer created
- [ ] S3 bucket created
- [ ] CloudFront distribution created
- [ ] GitHub secrets added
- [ ] Docker files created
- [ ] GitHub Actions workflows added
- [ ] Environment variables configured

### After Deployment

- [ ] Backend health check passing
- [ ] Frontend accessible via CloudFront
- [ ] Can download a YouTube video
- [ ] Can download an Instagram reel
- [ ] Audio-only download works
- [ ] Video trimming works (FFmpeg installed)
- [ ] Files cleanup working
- [ ] CloudWatch logs visible
- [ ] Auto-scaling configured
- [ ] Cost alerts set up

### Production Readiness

- [ ] Custom domain configured
- [ ] SSL certificate installed
- [ ] Rate limiting enabled
- [ ] Authentication implemented
- [ ] Database for user management (if needed)
- [ ] Backup strategy defined
- [ ] Monitoring and alerts configured
- [ ] Error tracking (Sentry, etc.)
- [ ] Performance optimization
- [ ] Security audit completed

---

## 🚀 Next Steps

1. **Custom Domain**: 
   - Purchase domain (Route 53 or external)
   - Create SSL certificate (AWS Certificate Manager)
   - Update CloudFront to use custom domain

2. **Enhanced Security**:
   - Add WAF (Web Application Firewall)
   - Implement API Gateway with API keys
   - Add authentication (Cognito)

3. **Advanced Features**:
   - Add Redis for caching
   - Implement queue system (SQS + Lambda)
   - Add database (RDS or DynamoDB)
   - WebSocket support for real-time progress

4. **Monitoring**:
   - CloudWatch dashboards
   - X-Ray for tracing
   - SNS alerts for errors

---

## 📚 Useful Commands

```bash
# View ECS service
aws ecs describe-services --cluster ytdlp-cluster --services ytdlp-service

# View running tasks
aws ecs list-tasks --cluster ytdlp-cluster

# View task logs
aws logs tail /ecs/ytdlp-backend --follow

# Update service (force new deployment)
aws ecs update-service --cluster ytdlp-cluster --service ytdlp-service --force-new-deployment

# Sync frontend to S3
aws s3 sync frontend/build/ s3://ytdlp-frontend-YOUR-NAME/ --delete

# Invalidate CloudFront
aws cloudfront create-invalidation --distribution-id E123 --paths "/*"

# Check ECR images
aws ecr list-images --repository-name ytdlp-backend
```

---

## 🎉 Success!

Once deployed, your application will:
- ✅ Automatically deploy when you push to GitHub
- ✅ Scale based on demand
- ✅ Be accessible worldwide via CloudFront CDN
- ✅ Have automatic SSL/HTTPS
- ✅ Store videos temporarily on EFS
- ✅ Have monitoring and logging

**Your production URLs**:
- Frontend: `https://d123456789.cloudfront.net`
- Backend API: `http://ytdlp-alb-123.us-east-1.elb.amazonaws.com`
- API Docs: `http://ytdlp-alb-123.us-east-1.elb.amazonaws.com/docs`

---

**Need Help?** Check AWS documentation or GitHub Actions logs for detailed error messages.
