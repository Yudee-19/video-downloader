# ⚡ Quick Command Reference - Redis Batch Downloads

## 🚀 Local Testing Commands

### Start Redis
```bash
# Docker (Recommended)
docker run -d -p 6379:6379 --name redis redis:7-alpine

# Windows WSL
wsl sudo service redis-server start

# Mac
brew services start redis

# Linux
sudo systemctl start redis-server

# Verify Redis is running
redis-cli ping  # Should return: PONG
```

### Start Application
```bash
# Quick start (Windows)
start-local-redis.bat

# Quick start (Linux/Mac)
chmod +x start-local-redis.sh
./start-local-redis.sh

# Manual backend
cd backend
pip install -r requirements.txt
export REDIS_HOST=localhost
export REDIS_PORT=6379
export MAX_PARALLEL_DOWNLOADS=3
python main.py

# Manual frontend
cd frontend
npm install
echo "REACT_APP_API_URL=http://localhost:8000" > .env.development
npm start
```

---

## 🌐 AWS Deployment Commands

### 1. Deploy Infrastructure
```bash
# Create stack with Redis
aws cloudformation create-stack \
    --stack-name ytdlp-infrastructure \
    --template-body file://aws/cloudformation-template.yaml \
    --capabilities CAPABILITY_IAM \
    --region us-east-1

# Wait for completion
aws cloudformation wait stack-create-complete \
    --stack-name ytdlp-infrastructure \
    --region us-east-1

# Get outputs
aws cloudformation describe-stacks \
    --stack-name ytdlp-infrastructure \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table
```

### 2. Get Important Values
```bash
# Save these as environment variables
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export REDIS_ENDPOINT=$(aws cloudformation describe-stacks --stack-name ytdlp-infrastructure --query 'Stacks[0].Outputs[?OutputKey==`RedisEndpoint`].OutputValue' --output text)
export ECR_URI=$(aws cloudformation describe-stacks --stack-name ytdlp-infrastructure --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryURI`].OutputValue' --output text)
export ALB_DNS=$(aws cloudformation describe-stacks --stack-name ytdlp-infrastructure --query 'Stacks[0].Outputs[?OutputKey==`ALBDNSName`].OutputValue' --output text)
export S3_BUCKET=$(aws cloudformation describe-stacks --stack-name ytdlp-infrastructure --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' --output text)
export CF_DIST_ID=$(aws cloudformation describe-stacks --stack-name ytdlp-infrastructure --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' --output text)

echo "Redis Endpoint: $REDIS_ENDPOINT"
echo "ECR URI: $ECR_URI"
echo "ALB DNS: $ALB_DNS"
```

### 3. Update Configuration Files
```bash
# Update task definition with Redis endpoint
# Edit aws/ecs-task-definition.json manually and replace:
# - YOUR_REDIS_ENDPOINT with $REDIS_ENDPOINT
# - YOUR_ACCOUNT_ID with $AWS_ACCOUNT_ID
```

### 4. Build and Push Backend
```bash
cd backend

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin $ECR_URI

# Build
docker build -t ytdlp-backend:latest .

# Tag
docker tag ytdlp-backend:latest $ECR_URI:latest

# Push
docker push $ECR_URI:latest
```

### 5. Deploy Backend to ECS
```bash
# Register task definition
aws ecs register-task-definition \
    --cli-input-json file://aws/ecs-task-definition.json \
    --region us-east-1

# Get subnet and security group IDs
export SUBNET1=$(aws cloudformation describe-stacks --stack-name ytdlp-infrastructure --query 'Stacks[0].Outputs[?OutputKey==`PublicSubnet1Id`].OutputValue' --output text)
export SUBNET2=$(aws cloudformation describe-stacks --stack-name ytdlp-infrastructure --query 'Stacks[0].Outputs[?OutputKey==`PublicSubnet2Id`].OutputValue' --output text)
export ECS_SG=$(aws cloudformation describe-stacks --stack-name ytdlp-infrastructure --query 'Stacks[0].Outputs[?OutputKey==`ECSSecurityGroupId`].OutputValue' --output text)
export TG_ARN=$(aws cloudformation describe-stacks --stack-name ytdlp-infrastructure --query 'Stacks[0].Outputs[?OutputKey==`ALBTargetGroupArn`].OutputValue' --output text)

# Create service
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

### 6. Deploy Frontend
```bash
cd frontend

# Create production env
echo "REACT_APP_API_URL=http://$ALB_DNS" > .env.production

# Build
npm install
npm run build

# Deploy to S3
aws s3 sync build/ s3://$S3_BUCKET/ --delete

# Invalidate CloudFront
aws cloudfront create-invalidation \
    --distribution-id $CF_DIST_ID \
    --paths "/*"
```

---

## 🔍 Monitoring Commands

### Check Service Status
```bash
# ECS service
aws ecs describe-services \
    --cluster ytdlp-cluster \
    --services ytdlp-service \
    --region us-east-1

# Running tasks
aws ecs list-tasks \
    --cluster ytdlp-cluster \
    --service-name ytdlp-service \
    --region us-east-1

# Task details
export TASK_ARN=$(aws ecs list-tasks --cluster ytdlp-cluster --service-name ytdlp-service --query 'taskArns[0]' --output text)
aws ecs describe-tasks \
    --cluster ytdlp-cluster \
    --tasks $TASK_ARN \
    --region us-east-1
```

### View Logs
```bash
# Tail backend logs
aws logs tail /ecs/ytdlp-backend --follow --region us-east-1

# Get last 100 lines
aws logs tail /ecs/ytdlp-backend --since 10m --region us-east-1

# Filter for errors
aws logs tail /ecs/ytdlp-backend --follow --filter-pattern "ERROR" --region us-east-1
```

### Check Redis
```bash
# Redis cluster status
aws elasticache describe-cache-clusters \
    --cache-cluster-id ytdlp-redis \
    --show-cache-node-info \
    --region us-east-1

# Connect to Redis (from EC2 or ECS task)
redis-cli -h $REDIS_ENDPOINT ping
redis-cli -h $REDIS_ENDPOINT INFO
redis-cli -h $REDIS_ENDPOINT DBSIZE
```

---

## 🧪 Testing Commands

### Test Local API
```bash
# Health check
curl http://localhost:8000/

# Single download
curl -X POST http://localhost:8000/download \
    -H "Content-Type: application/json" \
    -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Batch download
curl -X POST http://localhost:8000/batch-download \
    -H "Content-Type: application/json" \
    -d '{
        "urls": [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=9bZkp7q19f0"
        ],
        "audio_only": false
    }'

# Check status (replace FILE_ID)
curl http://localhost:8000/status/FILE_ID

# Check batch status (replace BATCH_ID)
curl http://localhost:8000/batch-status/BATCH_ID
```

### Test Production API
```bash
# Replace with your ALB DNS
export API_URL="http://your-alb-dns.amazonaws.com"

curl $API_URL/
curl -X POST $API_URL/download -H "Content-Type: application/json" -d '{"url":"https://youtube.com/watch?v=xxx"}'
```

---

## 🔄 Update/Restart Commands

### Update Backend Code
```bash
# Rebuild and push
cd backend
docker build -t ytdlp-backend:latest .
docker push $ECR_URI:latest

# Force new deployment
aws ecs update-service \
    --cluster ytdlp-cluster \
    --service ytdlp-service \
    --force-new-deployment \
    --region us-east-1
```

### Update Frontend
```bash
cd frontend
npm run build
aws s3 sync build/ s3://$S3_BUCKET/ --delete
aws cloudfront create-invalidation --distribution-id $CF_DIST_ID --paths "/*"
```

### Scale ECS Service
```bash
# Scale up
aws ecs update-service \
    --cluster ytdlp-cluster \
    --service ytdlp-service \
    --desired-count 2 \
    --region us-east-1

# Scale down
aws ecs update-service \
    --cluster ytdlp-cluster \
    --service ytdlp-service \
    --desired-count 0 \
    --region us-east-1
```

### Update Task Definition
```bash
# After editing aws/ecs-task-definition.json
aws ecs register-task-definition \
    --cli-input-json file://aws/ecs-task-definition.json \
    --region us-east-1

# Update service to use new task definition
aws ecs update-service \
    --cluster ytdlp-cluster \
    --service ytdlp-service \
    --task-definition ytdlp-backend \
    --force-new-deployment \
    --region us-east-1
```

---

## 🗑️ Cleanup Commands

### Delete Everything
```bash
# Stop ECS service
aws ecs update-service \
    --cluster ytdlp-cluster \
    --service ytdlp-service \
    --desired-count 0 \
    --region us-east-1

# Wait 30 seconds
sleep 30

# Delete ECS service
aws ecs delete-service \
    --cluster ytdlp-cluster \
    --service ytdlp-service \
    --force \
    --region us-east-1

# Delete CloudFormation stack (deletes everything)
aws cloudformation delete-stack \
    --stack-name ytdlp-infrastructure \
    --region us-east-1

# Empty and delete S3 bucket
aws s3 rm s3://$S3_BUCKET/ --recursive
aws s3 rb s3://$S3_BUCKET/
```

### Cleanup Local Docker
```bash
# Stop containers
docker stop redis

# Remove containers
docker rm redis

# Remove images
docker rmi redis:7-alpine ytdlp-backend
```

---

## 📊 Useful Queries

### Cost Analysis
```bash
# Current month costs
aws ce get-cost-and-usage \
    --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
    --granularity MONTHLY \
    --metrics BlendedCost

# By service
aws ce get-cost-and-usage \
    --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=DIMENSION,Key=SERVICE
```

### List Resources
```bash
# ECR images
aws ecr list-images \
    --repository-name ytdlp-backend \
    --region us-east-1

# ECS clusters
aws ecs list-clusters --region us-east-1

# ElastiCache clusters
aws elasticache describe-cache-clusters --region us-east-1

# S3 buckets
aws s3 ls

# CloudFront distributions
aws cloudfront list-distributions
```

---

## 🐛 Debugging Commands

### Check Security Groups
```bash
# ECS security group
aws ec2 describe-security-groups \
    --group-ids $ECS_SG \
    --region us-east-1

# Redis security group
aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=ytdlp-redis-sg" \
    --region us-east-1
```

### Check Network Connectivity
```bash
# From ECS task, install telnet and test
telnet $REDIS_ENDPOINT 6379

# Or use AWS CLI to check VPC
aws ec2 describe-vpcs --region us-east-1
aws ec2 describe-subnets --region us-east-1
```

### View CloudWatch Metrics
```bash
# ECS CPU utilization
aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name CPUUtilization \
    --dimensions Name=ServiceName,Value=ytdlp-service Name=ClusterName,Value=ytdlp-cluster \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Average \
    --region us-east-1
```

---

## 💡 Pro Tips

```bash
# Create aliases for common commands
alias ytdlp-logs='aws logs tail /ecs/ytdlp-backend --follow'
alias ytdlp-status='aws ecs describe-services --cluster ytdlp-cluster --services ytdlp-service'
alias ytdlp-restart='aws ecs update-service --cluster ytdlp-cluster --service ytdlp-service --force-new-deployment'

# Save outputs to file
aws cloudformation describe-stacks --stack-name ytdlp-infrastructure > outputs.json

# Watch logs and grep for specific patterns
aws logs tail /ecs/ytdlp-backend --follow | grep "batch_id"
```

---

**Quick reference complete! Bookmark this file for easy access to all commands. 🚀**
