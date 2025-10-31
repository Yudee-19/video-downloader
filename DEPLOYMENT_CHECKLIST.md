# 📋 AWS Deployment Checklist

Use this checklist to ensure you complete all steps for deploying your application to AWS.

## ⚙️ Pre-Deployment Setup

### AWS Account Setup
- [ ] Create AWS account
- [ ] Enable MFA for root account
- [ ] Set up billing alerts (recommend: $50/month alert)
- [ ] Create IAM user `github-actions-deployer`
- [ ] Save Access Key ID and Secret Access Key securely

### Local Environment Setup
- [ ] Install AWS CLI: `pip install awscli`
- [ ] Configure AWS CLI: `aws configure`
- [ ] Install Docker Desktop
- [ ] Test Docker: `docker --version`
- [ ] Install Git
- [ ] Create GitHub account

### Repository Setup
- [ ] Initialize Git repository
- [ ] Create GitHub repository
- [ ] Push code to GitHub
- [ ] Create `deployment` branch: `git checkout -b deployment`

---

## 🏗️ Infrastructure Setup

### 1. Deploy CloudFormation Stack (Easiest Method)
```bash
# Deploy the complete infrastructure
aws cloudformation create-stack \
    --stack-name ytdlp-infrastructure \
    --template-body file://aws/cloudformation-template.yaml \
    --capabilities CAPABILITY_IAM \
    --region us-east-1

# Wait for completion (5-10 minutes)
aws cloudformation wait stack-create-complete \
    --stack-name ytdlp-infrastructure \
    --region us-east-1

# Get outputs
aws cloudformation describe-stacks \
    --stack-name ytdlp-infrastructure \
    --region us-east-1 \
    --query 'Stacks[0].Outputs'
```

**Save These Values:**
- [ ] VPC ID
- [ ] Subnet IDs (2)
- [ ] ECS Cluster Name
- [ ] ALB DNS Name
- [ ] ALB Target Group ARN
- [ ] EFS File System ID
- [ ] ECR Repository URI
- [ ] ECS Security Group ID
- [ ] S3 Bucket Name
- [ ] CloudFront Domain
- [ ] CloudFront Distribution ID

### 2. Manual Setup (Alternative)

If you prefer manual setup or CloudFormation fails:

#### ECR Repository
- [ ] Create ECR repository: `ytdlp-backend`
- [ ] Note the repository URI

#### VPC & Networking
- [ ] Create or use default VPC
- [ ] Ensure 2+ public subnets in different AZs
- [ ] Internet Gateway attached
- [ ] Route tables configured

#### Security Groups
- [ ] Create ALB security group (ports 80, 443)
- [ ] Create ECS security group (port 8000 from ALB)
- [ ] Create EFS security group (port 2049 from ECS)

#### EFS File System
- [ ] Create EFS file system
- [ ] Create mount targets in all subnets
- [ ] Attach EFS security group
- [ ] Note File System ID

#### Application Load Balancer
- [ ] Create ALB (internet-facing)
- [ ] Select 2+ subnets
- [ ] Attach ALB security group
- [ ] Create target group (IP, port 8000, health check `/`)
- [ ] Create HTTP listener (port 80)
- [ ] Note ALB DNS name and Target Group ARN

#### ECS Cluster
- [ ] Create ECS cluster: `ytdlp-cluster`
- [ ] Enable Container Insights

#### S3 Bucket
- [ ] Create S3 bucket: `ytdlp-frontend-YOUR-NAME`
- [ ] Enable static website hosting
- [ ] Set bucket policy for public read
- [ ] Note bucket name

#### CloudFront Distribution
- [ ] Create CloudFront distribution
- [ ] Origin: S3 bucket website endpoint
- [ ] Default root object: `index.html`
- [ ] Create error responses (403, 404 → /index.html)
- [ ] Note CloudFront domain and distribution ID

---

## 📝 Update Configuration Files

### Update ECS Task Definition
Edit `aws/ecs-task-definition.json`:
- [ ] Replace `YOUR_ACCOUNT_ID` with your AWS account ID
- [ ] Replace `YOUR_EFS_ID` with your EFS file system ID
- [ ] Update `CORS_ORIGINS` with CloudFront domain
- [ ] Update `executionRoleArn` ARN
- [ ] Update `taskRoleArn` ARN

### Create CloudWatch Log Group
```bash
aws logs create-log-group \
    --log-group-name /ecs/ytdlp-backend \
    --region us-east-1
```
- [ ] CloudWatch log group created

---

## 🔑 GitHub Secrets Configuration

Go to GitHub → Repository → Settings → Secrets and variables → Actions

Add these secrets:

- [ ] `AWS_ACCESS_KEY_ID` - From IAM user
- [ ] `AWS_SECRET_ACCESS_KEY` - From IAM user
- [ ] `AWS_REGION` - `us-east-1` (or your region)
- [ ] `ECR_REPOSITORY` - `ytdlp-backend`
- [ ] `ECS_CLUSTER` - `ytdlp-cluster`
- [ ] `ECS_SERVICE` - `ytdlp-service`
- [ ] `S3_BUCKET` - Your S3 bucket name
- [ ] `CLOUDFRONT_DISTRIBUTION_ID` - From CloudFront
- [ ] `API_URL` - ALB DNS name (e.g., `http://ytdlp-alb-xxx.us-east-1.elb.amazonaws.com`)

---

## 🐳 Initial Backend Deployment

### Build and Push Docker Image

```bash
# Navigate to backend
cd backend

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -t ytdlp-backend:latest .

# Tag image
docker tag ytdlp-backend:latest \
    YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ytdlp-backend:latest

# Push image
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ytdlp-backend:latest
```

- [ ] Docker image built
- [ ] Docker image pushed to ECR

### Create ECS Service

```bash
# Register task definition
aws ecs register-task-definition \
    --cli-input-json file://aws/ecs-task-definition.json

# Create ECS service
aws ecs create-service \
    --cluster ytdlp-cluster \
    --service-name ytdlp-service \
    --task-definition ytdlp-backend \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=ytdlp-backend,containerPort=8000"
```

- [ ] Task definition registered
- [ ] ECS service created
- [ ] Service is running (check ECS console)

### Test Backend

```bash
# Test health check
curl http://YOUR-ALB-DNS-NAME/

# Should return: {"message": "YouTube & Instagram Downloader API"}
```

- [ ] Backend health check passing
- [ ] Can access API documentation at `/docs`

---

## 🌐 Initial Frontend Deployment

### Build and Deploy Frontend

```bash
# Navigate to frontend
cd frontend

# Update .env.production with ALB URL
echo "REACT_APP_API_URL=http://YOUR-ALB-DNS-NAME" > .env.production

# Install dependencies
npm install

# Build
npm run build

# Deploy to S3
aws s3 sync build/ s3://YOUR-BUCKET-NAME/ --delete

# Invalidate CloudFront
aws cloudfront create-invalidation \
    --distribution-id YOUR-DISTRIBUTION-ID \
    --paths "/*"
```

- [ ] Frontend built successfully
- [ ] Files uploaded to S3
- [ ] CloudFront cache invalidated

### Test Frontend

- [ ] Access CloudFront domain
- [ ] Frontend loads correctly
- [ ] Can see the download form

---

## ✅ Full Application Testing

### Test YouTube Download
- [ ] Enter YouTube URL: `https://www.youtube.com/watch?v=jNQXAC9IVRw`
- [ ] Click "Download"
- [ ] Status shows "Downloading..."
- [ ] Download completes
- [ ] Can download file

### Test Instagram Download
- [ ] Enter Instagram reel URL
- [ ] Click "Download"
- [ ] Status shows "Downloading..."
- [ ] Download completes
- [ ] Can download file

### Test Audio Download
- [ ] Enter YouTube URL
- [ ] Check "Audio Only (MP3)"
- [ ] Click "Download"
- [ ] Downloads MP3 file

### Test Video Trimming (YouTube only)
- [ ] Enter YouTube URL
- [ ] Set start time: `00:00:10`
- [ ] Set end time: `00:00:30`
- [ ] Click "Download"
- [ ] Downloads trimmed video

---

## 🚀 CI/CD Pipeline Testing

### Test Backend Pipeline

```bash
# Make a change to backend
echo "# Test deployment" >> backend/README.md

# Commit and push
git add .
git commit -m "Test backend CI/CD"
git push origin deployment
```

- [ ] GitHub Actions triggered
- [ ] Docker image built
- [ ] Image pushed to ECR
- [ ] ECS service updated
- [ ] New task running
- [ ] Health checks passing

### Test Frontend Pipeline

```bash
# Make a change to frontend
echo "# Test deployment" >> frontend/README.md

# Commit and push
git add .
git commit -m "Test frontend CI/CD"
git push origin deployment
```

- [ ] GitHub Actions triggered
- [ ] React app built
- [ ] Files synced to S3
- [ ] CloudFront invalidated
- [ ] Changes visible on CloudFront domain

---

## 🔐 Security Hardening

### Backend Security
- [ ] Update CORS origins in task definition (remove wildcard)
- [ ] Enable HTTPS on ALB (add SSL certificate)
- [ ] Set up AWS WAF (optional)
- [ ] Enable VPC Flow Logs
- [ ] Review IAM roles (principle of least privilege)

### Frontend Security
- [ ] Use CloudFront custom domain with SSL
- [ ] Enable CloudFront origin access identity
- [ ] Add security headers
- [ ] Enable S3 bucket encryption

### Application Security
- [ ] Add rate limiting
- [ ] Implement authentication (if needed)
- [ ] Add input validation
- [ ] Set file size limits
- [ ] Add virus scanning (optional)

---

## 📊 Monitoring & Alerts

### CloudWatch Alarms
- [ ] Create alarm for ECS CPU > 80%
- [ ] Create alarm for ECS Memory > 80%
- [ ] Create alarm for ALB 5xx errors
- [ ] Create alarm for ALB target health
- [ ] Create alarm for EFS throughput

### CloudWatch Dashboard
- [ ] Create dashboard with key metrics
- [ ] Add ECS service metrics
- [ ] Add ALB metrics
- [ ] Add S3/CloudFront metrics

### CloudWatch Logs
- [ ] Verify backend logs in `/ecs/ytdlp-backend`
- [ ] Set log retention (7 days recommended)
- [ ] Create log insights queries

---

## 💰 Cost Optimization

- [ ] Enable ECS Service Auto Scaling
- [ ] Set minimum tasks to 0 for non-prod
- [ ] Enable EFS Infrequent Access
- [ ] Set S3 lifecycle policies
- [ ] Delete old ECR images
- [ ] Review data transfer costs
- [ ] Set up cost alerts

---

## 🎯 Production Readiness

### Custom Domain (Optional)
- [ ] Purchase domain (Route 53 or external)
- [ ] Request SSL certificate (AWS Certificate Manager)
- [ ] Update CloudFront with custom domain
- [ ] Update ALB with SSL certificate
- [ ] Update DNS records
- [ ] Update CORS origins in backend

### Backup Strategy
- [ ] Enable EFS backups
- [ ] S3 versioning enabled
- [ ] Database backups (if added)
- [ ] Document recovery procedures

### Documentation
- [ ] Update README with production URLs
- [ ] Document deployment process
- [ ] Create runbook for common issues
- [ ] Document cost estimates

---

## 🐛 Common Issues Checklist

### Backend Not Starting
- [ ] Check CloudWatch logs
- [ ] Verify security group rules
- [ ] Check EFS mount
- [ ] Verify IAM roles
- [ ] Check task definition

### Frontend Not Loading
- [ ] Check S3 bucket permissions
- [ ] Verify CloudFront settings
- [ ] Check API URL in build
- [ ] Review CloudFront error pages

### CORS Errors
- [ ] Verify backend CORS_ORIGINS includes CloudFront domain
- [ ] Check ALB listener rules
- [ ] Verify security group rules

### Downloads Failing
- [ ] Check EFS storage space
- [ ] Verify FFmpeg installed in container
- [ ] Check yt-dlp version
- [ ] Review CloudWatch logs

---

## ✅ Final Verification

- [ ] Backend API accessible via ALB
- [ ] Frontend accessible via CloudFront
- [ ] Can download YouTube videos
- [ ] Can download Instagram videos
- [ ] Audio download works
- [ ] Video trimming works
- [ ] CI/CD pipeline works for backend
- [ ] CI/CD pipeline works for frontend
- [ ] Monitoring and alerts configured
- [ ] Security best practices applied
- [ ] Documentation updated
- [ ] Cost alerts configured

---

## 🎉 Deployment Complete!

Once all items are checked, your application is fully deployed to AWS with CI/CD!

**Next Steps:**
1. Share your CloudFront URL with users
2. Monitor costs and usage
3. Plan for scaling and improvements
4. Consider adding authentication
5. Add more features from the roadmap

---

## 📞 Support Resources

- **AWS Support**: https://console.aws.amazon.com/support/
- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **React Docs**: https://react.dev/
- **yt-dlp Issues**: https://github.com/yt-dlp/yt-dlp/issues

---

**Remember:** Save all important values (IDs, ARNs, URLs) in a secure location!
