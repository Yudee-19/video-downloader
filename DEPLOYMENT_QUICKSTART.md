# 🚀 Quick Deployment Reference

**Quick commands for deploying to AWS. See DEPLOYMENT_GUIDE.md for full details.**

## 📋 Prerequisites Checklist
- [ ] AWS Account created
- [ ] AWS CLI installed and configured
- [ ] Docker Desktop installed
- [ ] GitHub repository created
- [ ] Code pushed to GitHub

---

## ⚡ Quick Deploy (30 Minutes)

### 1. Deploy Infrastructure (5 min)

```bash
# Deploy everything with CloudFormation
aws cloudformation create-stack \
    --stack-name ytdlp-infrastructure \
    --template-body file://aws/cloudformation-template.yaml \
    --capabilities CAPABILITY_IAM \
    --region us-east-1

# Wait for completion
aws cloudformation wait stack-create-complete \
    --stack-name ytdlp-infrastructure
```

### 2. Get Stack Outputs (1 min)

```bash
# Get all outputs
aws cloudformation describe-stacks \
    --stack-name ytdlp-infrastructure \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table
```

**Save these values:**
- ECRRepositoryURI
- ECSClusterName
- ALBDNSName
- CloudFrontDomain
- CloudFrontDistributionId
- S3BucketName
- EFSFileSystemId
- ECSSecurityGroupId
- PublicSubnet1Id
- PublicSubnet2Id
- ALBTargetGroupArn

### 3. Update Configuration Files (5 min)

```bash
# Get your AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Update task definition (replace placeholders)
sed -i "s/YOUR_ACCOUNT_ID/$AWS_ACCOUNT_ID/g" aws/ecs-task-definition.json
sed -i "s/YOUR_EFS_ID/fs-XXXXX/g" aws/ecs-task-definition.json
sed -i "s/YOUR_CLOUDFRONT_DOMAIN/dXXXXXX.cloudfront.net/g" aws/ecs-task-definition.json
```

### 4. Create CloudWatch Log Group (1 min)

```bash
aws logs create-log-group \
    --log-group-name /ecs/ytdlp-backend \
    --region us-east-1
```

### 5. Deploy Backend (10 min)

```bash
cd backend

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t ytdlp-backend:latest .
docker tag ytdlp-backend:latest \
    $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ytdlp-backend:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ytdlp-backend:latest

# Register task definition
aws ecs register-task-definition \
    --cli-input-json file://../aws/ecs-task-definition.json

# Create service (replace subnet and security group IDs)
aws ecs create-service \
    --cluster ytdlp-cluster \
    --service-name ytdlp-service \
    --task-definition ytdlp-backend \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-XXX,subnet-YYY],securityGroups=[sg-XXX],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:region:account:targetgroup/ytdlp-tg/xxx,containerName=ytdlp-backend,containerPort=8000"
```

### 6. Deploy Frontend (5 min)

```bash
cd ../frontend

# Update API URL
echo "REACT_APP_API_URL=http://YOUR-ALB-DNS" > .env.production

# Build and deploy
npm install
npm run build

# Deploy to S3
aws s3 sync build/ s3://YOUR-BUCKET-NAME/ --delete

# Invalidate CloudFront
aws cloudfront create-invalidation \
    --distribution-id YOUR-DIST-ID \
    --paths "/*"
```

### 7. Setup GitHub Secrets (3 min)

Add these secrets in GitHub → Settings → Secrets:

```
AWS_ACCESS_KEY_ID: <your-key>
AWS_SECRET_ACCESS_KEY: <your-secret>
AWS_REGION: us-east-1
ECR_REPOSITORY: ytdlp-backend
ECS_CLUSTER: ytdlp-cluster
ECS_SERVICE: ytdlp-service
S3_BUCKET: <your-bucket>
CLOUDFRONT_DISTRIBUTION_ID: <your-id>
API_URL: http://<your-alb-dns>
```

### 8. Test Deployment (5 min)

```bash
# Test backend
curl http://YOUR-ALB-DNS/

# Open frontend
open https://YOUR-CLOUDFRONT-DOMAIN

# Push to trigger CI/CD
git add .
git commit -m "Deploy to AWS"
git push origin main
```

---

## 🔄 Daily Operations

### Deploy Backend Changes
```bash
git add backend/
git commit -m "Update backend"
git push origin main
# GitHub Actions will automatically deploy
```

### Deploy Frontend Changes
```bash
git add frontend/
git commit -m "Update frontend"
git push origin main
# GitHub Actions will automatically deploy
```

### Manual Backend Update
```bash
aws ecs update-service \
    --cluster ytdlp-cluster \
    --service ytdlp-service \
    --force-new-deployment
```

### Check Backend Logs
```bash
aws logs tail /ecs/ytdlp-backend --follow
```

### Check Service Status
```bash
aws ecs describe-services \
    --cluster ytdlp-cluster \
    --services ytdlp-service
```

---

## 🐛 Quick Troubleshooting

### Backend Not Starting
```bash
# Check service events
aws ecs describe-services --cluster ytdlp-cluster --services ytdlp-service

# Check logs
aws logs tail /ecs/ytdlp-backend --follow

# Check task status
aws ecs list-tasks --cluster ytdlp-cluster --service ytdlp-service
```

### Frontend Not Updating
```bash
# Invalidate CloudFront
aws cloudfront create-invalidation \
    --distribution-id YOUR-DIST-ID \
    --paths "/*"

# Check S3 files
aws s3 ls s3://YOUR-BUCKET-NAME/
```

### CORS Errors
Update backend environment in task definition:
```json
{
  "name": "CORS_ORIGINS",
  "value": "https://YOUR-CLOUDFRONT-DOMAIN"
}
```

---

## 💰 Cost Monitoring

```bash
# Check current month costs
aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-31 \
    --granularity MONTHLY \
    --metrics BlendedCost
```

---

## 🗑️ Cleanup Everything

```bash
# Delete ECS service
aws ecs update-service \
    --cluster ytdlp-cluster \
    --service ytdlp-service \
    --desired-count 0

aws ecs delete-service \
    --cluster ytdlp-cluster \
    --service ytdlp-service

# Delete CloudFormation stack (deletes all resources)
aws cloudformation delete-stack \
    --stack-name ytdlp-infrastructure

# Empty and delete S3 bucket
aws s3 rm s3://YOUR-BUCKET-NAME/ --recursive
aws s3 rb s3://YOUR-BUCKET-NAME/
```

---

## 📚 Useful Commands

```bash
# Get AWS Account ID
aws sts get-caller-identity

# List ECR images
aws ecr list-images --repository-name ytdlp-backend

# List running tasks
aws ecs list-tasks --cluster ytdlp-cluster

# Get task details
aws ecs describe-tasks --cluster ytdlp-cluster --tasks TASK-ID

# Force new deployment
aws ecs update-service \
    --cluster ytdlp-cluster \
    --service ytdlp-service \
    --force-new-deployment

# Scale ECS service
aws ecs update-service \
    --cluster ytdlp-cluster \
    --service ytdlp-service \
    --desired-count 2
```

---

## 🎯 Success Verification

Your deployment is successful when:
- ✅ `curl http://YOUR-ALB-DNS/` returns API message
- ✅ Frontend loads at CloudFront URL
- ✅ Can download a YouTube video
- ✅ Can download an Instagram video
- ✅ GitHub Actions runs successfully

---

## 📞 Get Help

- **Full Guide**: See `DEPLOYMENT_GUIDE.md`
- **Checklist**: See `DEPLOYMENT_CHECKLIST.md`
- **AWS Support**: https://console.aws.amazon.com/support/

---

**⏱️ Total Time: ~30 minutes for first deployment**
**📝 Remember to save all IDs and URLs in a secure note!**
