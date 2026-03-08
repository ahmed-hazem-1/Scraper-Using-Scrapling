#!/bin/bash
# Google Cloud Run Deployment Script
# This script automates the deployment of Scrapling Search API to Cloud Run

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="scrapling-search-api"
REGION="${REGION:-us-central1}"
MEMORY="${MEMORY:-1Gi}"
CPU="${CPU:-1}"
TIMEOUT="${TIMEOUT:-60}"
MAX_INSTANCES="${MAX_INSTANCES:-10}"
MIN_INSTANCES="${MIN_INSTANCES:-0}"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Cloud Run Deployment Script${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No GCP project configured${NC}"
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${YELLOW}Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Service Name: $SERVICE_NAME"
echo "  Region: $REGION"
echo "  Memory: $MEMORY"
echo "  CPU: $CPU"
echo "  Timeout: ${TIMEOUT}s"
echo "  Min Instances: $MIN_INSTANCES"
echo "  Max Instances: $MAX_INSTANCES"
echo ""

# Confirmation
read -p "Deploy to Cloud Run? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""
echo -e "${YELLOW}Step 1: Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID
echo -e "${GREEN}✓ APIs enabled${NC}"

echo ""
echo -e "${YELLOW}Step 2: Building and deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory $MEMORY \
  --cpu $CPU \
  --timeout $TIMEOUT \
  --max-instances $MAX_INSTANCES \
  --min-instances $MIN_INSTANCES \
  --project $PROJECT_ID

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}================================${NC}"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)' --project=$PROJECT_ID 2>/dev/null)

if [ ! -z "$SERVICE_URL" ]; then
    echo ""
    echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"
    echo ""
    echo "Test endpoints:"
    echo "  Health: ${SERVICE_URL}/health"
    echo "  Docs: ${SERVICE_URL}/docs"
    echo "  Example: ${SERVICE_URL}/search?q=python&limit=5&engine=duckduckgo"
    echo ""
    
    # Test health endpoint
    echo -e "${YELLOW}Testing health endpoint...${NC}"
    sleep 5  # Wait for deployment to stabilize
    if curl -s "${SERVICE_URL}/health" | grep -q "ok"; then
        echo -e "${GREEN}✓ Service is healthy!${NC}"
    else
        echo -e "${RED}✗ Health check failed${NC}"
    fi
fi

echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "  View logs: gcloud run services logs read $SERVICE_NAME --region $REGION --project $PROJECT_ID"
echo "  Get URL: gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)' --project $PROJECT_ID"
echo "  Delete: gcloud run services delete $SERVICE_NAME --region $REGION --project $PROJECT_ID"
