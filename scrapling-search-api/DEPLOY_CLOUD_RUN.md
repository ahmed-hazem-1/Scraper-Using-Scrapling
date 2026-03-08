# Google Cloud Run Deployment Guide

## Quick Start

### Automated Deployment (Recommended)

**Linux/Mac:**
```bash
chmod +x deploy-cloud-run.sh
./deploy-cloud-run.sh
```

**Windows (PowerShell):**
```powershell
.\deploy-cloud-run.ps1
```

The script will:
1. Enable required Google Cloud APIs
2. Build and deploy your application
3. Configure Cloud Run settings
4. Test the deployed service
5. Display the service URL

### Test Locally First

Before deploying, test the Docker image locally:

**Linux/Mac:**
```bash
chmod +x test-docker.sh
./test-docker.sh
```

**Windows (PowerShell):**
```powershell
.\test-docker.ps1
```

---

## Prerequisites
- Google Cloud SDK installed (`gcloud` CLI)
- Google Cloud project created
- Billing enabled on your project
- Docker installed locally (for testing)

## Deployment Steps

### 1. Authenticate with Google Cloud
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### 2. Enable Required APIs
```bash
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 3. Build and Deploy to Cloud Run (Direct)
```bash
# Navigate to project directory
cd scrapling-search-api

# Deploy directly (Cloud Build will build the image for you)
gcloud run deploy scrapling-search-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60s \
  --max-instances 10 \
  --min-instances 0
```

### 4. Alternative: Build Locally and Push
```bash
# Set variables
PROJECT_ID="your-project-id"
SERVICE_NAME="scrapling-search-api"
REGION="us-central1"

# Build Docker image
docker build -t gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest .

# Test locally
docker run -p 8080:8080 -e PORT=8080 gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest

# Push to Google Container Registry
docker push gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest

# Deploy to Cloud Run
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1
```

## Configuration

### Environment Variables (Optional)
If you need custom configuration:
```bash
gcloud run deploy scrapling-search-api \
  --set-env-vars="LOG_LEVEL=INFO,MAX_RETRIES=3,REQUEST_DELAY=2.0"
```

### Memory and CPU Recommendations
- **Development/Testing**: 512Mi RAM, 1 CPU
- **Production (100-1000 req/day)**: 1Gi RAM, 1 CPU
- **High Traffic**: 2Gi RAM, 2 CPU

### Timeout Settings
- Set based on expected search response time
- Recommended: 60s for search operations
- Default Cloud Run timeout: 300s (5 minutes)

## Cost Estimation (as of 2026)

### Cloud Run Pricing (us-central1)
- **CPU**: $0.00002400 per vCPU-second
- **Memory**: $0.00000250 per GiB-second
- **Requests**: $0.40 per million requests
- **Free tier**: 2 million requests/month, 360,000 vCPU-seconds, 180,000 GiB-seconds

### Example: 1,000 requests/day (~30K/month)
- Requests: 30,000 × $0.40/1M = **$0.01**
- CPU (avg 2s/req): 30,000 × 2 × $0.000024 = **$1.44**
- Memory (512Mi, 2s/req): 30,000 × 2 × 0.5 × $0.0000025 = **$0.08**
- **Total: ~$1.53/month** (well within free tier!)

## Post-Deployment

### Get Service URL
```bash
gcloud run services describe scrapling-search-api --region us-central1 --format 'value(status.url)'
```

### Test Deployed API
```bash
# Get your service URL
SERVICE_URL=$(gcloud run services describe scrapling-search-api --region us-central1 --format 'value(status.url)')

# Test health endpoint
curl ${SERVICE_URL}/health

# Test search endpoint
curl "${SERVICE_URL}/search?q=python&limit=5"
```

### View Logs
```bash
gcloud run services logs read scrapling-search-api --region us-central1
```

### Monitor Performance
```bash
# View metrics in Cloud Console
open "https://console.cloud.google.com/run/detail/${REGION}/scrapling-search-api/metrics"
```

## API Endpoints

Your deployed API will have:
- Health: `https://your-service-url/health`
- Search: `https://your-service-url/search?q=QUERY&limit=10`
- Docs: `https://your-service-url/docs`

## Active Engines

✅ **DuckDuckGo** (Primary): Best accuracy, bypasses bot detection  
⚠️ **Bing** (Backup): May return generic results due to bot detection  
❌ **Google**: Disabled (Playwright sync API incompatible with async FastAPI)

## Troubleshooting

### Container Fails to Start
Check logs: `gcloud run services logs read scrapling-search-api --limit 50`

### Port Issues
Cloud Run sets `PORT` environment variable automatically. Dockerfile uses `${PORT:-8080}`.

### Timeout Errors
Increase timeout: `--timeout 120s` in deploy command

### Memory Issues
Increase memory: `--memory 1Gi` in deploy command

### Cold Start Performance
Set min instances: `--min-instances 1` (costs more but faster response)

## Security Best Practices

### 1. Use Authenticated Access (Production)
```bash
# Remove --allow-unauthenticated
# Add authentication
gcloud run deploy scrapling-search-api --no-allow-unauthenticated
```

### 2. Set Up CORS (Already configured in code)
App allows all origins by default. Update `app/main.py` for production:
```python
allow_origins=["https://yourdomain.com"]
```

### 3. Rate Limiting
Consider adding Cloud Armor for DDoS protection:
```bash
# Enable Cloud Armor
gcloud compute security-policies create rate-limit-policy \
    --description "Rate limiting policy"
```

### 4. Use Secret Manager for Sensitive Data
```bash
# Store secrets
echo "your-api-key" | gcloud secrets create api-key --data-file=-

# Grant access
gcloud secrets add-iam-policy-binding api-key \
    --member serviceAccount:YOUR_SERVICE_ACCOUNT \
    --role roles/secretmanager.secretAccessor

# Use in Cloud Run
gcloud run deploy scrapling-search-api \
    --update-secrets=API_KEY=api-key:latest
```

## Cleanup

### Delete Service
```bash
gcloud run services delete scrapling-search-api --region us-central1
```

### Delete Container Images
```bash
gcloud container images delete gcr.io/${PROJECT_ID}/scrapling-search-api:latest
```

## Support

For issues or questions:
- Check logs: `gcloud run services logs read`
- Cloud Run docs: https://cloud.google.com/run/docs
- FastAPI docs: https://fastapi.tiangolo.com
