#!/bin/bash
# Local Docker Testing Script
# Test the Docker image locally before deploying to Cloud Run

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

IMAGE_NAME="scrapling-search-api"
PORT="${PORT:-8080}"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Local Docker Testing${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Building Docker image...${NC}"
docker build -t $IMAGE_NAME:test .
echo -e "${GREEN}✓ Image built successfully${NC}"
echo ""

echo -e "${YELLOW}Step 2: Running container on port $PORT...${NC}"
# Stop any existing container
docker stop $IMAGE_NAME 2>/dev/null || true
docker rm $IMAGE_NAME 2>/dev/null || true

# Run container
docker run -d \
    --name $IMAGE_NAME \
    -p $PORT:$PORT \
    -e PORT=$PORT \
    $IMAGE_NAME:test

echo -e "${GREEN}✓ Container started${NC}"
echo ""

echo -e "${YELLOW}Step 3: Waiting for service to start...${NC}"
sleep 5

# Test health endpoint
echo -e "${YELLOW}Step 4: Testing endpoints...${NC}"
if curl -s "http://localhost:$PORT/health" | grep -q "ok"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
    docker logs $IMAGE_NAME
    exit 1
fi

# Test search endpoint
echo -e "${YELLOW}Testing search endpoint...${NC}"
if curl -s "http://localhost:$PORT/search?q=python&limit=1&engine=duckduckgo" | grep -q "python"; then
    echo -e "${GREEN}✓ Search endpoint working${NC}"
else
    echo -e "${RED}✗ Search endpoint failed${NC}"
    docker logs $IMAGE_NAME
    exit 1
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}All tests passed!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Service is running at: http://localhost:$PORT"
echo "  Health: http://localhost:$PORT/health"
echo "  Docs: http://localhost:$PORT/docs"
echo "  Search: http://localhost:$PORT/search?q=test&limit=5&engine=duckduckgo"
echo ""
echo "View logs: docker logs $IMAGE_NAME"
echo "Stop container: docker stop $IMAGE_NAME"
echo ""
echo -e "${GREEN}Ready for Cloud Run deployment!${NC}"
