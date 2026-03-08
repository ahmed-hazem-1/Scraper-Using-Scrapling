# Local Docker Testing Script (PowerShell)
# Test the Docker image locally before deploying to Cloud Run

$ErrorActionPreference = "Stop"

$ImageName = "scrapling-search-api"
$Port = if ($env:PORT) { $env:PORT } else { 8080 }

Write-Host "================================" -ForegroundColor Green
Write-Host "Local Docker Testing" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "Error: Docker is not running" -ForegroundColor Red
    exit 1
}

Write-Host "Step 1: Building Docker image..." -ForegroundColor Yellow
docker build -t "${ImageName}:test" .
Write-Host "✓ Image built successfully" -ForegroundColor Green
Write-Host ""

Write-Host "Step 2: Running container on port $Port..." -ForegroundColor Yellow
# Stop any existing container
docker stop $ImageName 2>$null
docker rm $ImageName 2>$null

# Run container
docker run -d `
    --name $ImageName `
    -p "${Port}:${Port}" `
    -e PORT=$Port `
    "${ImageName}:test"

Write-Host "✓ Container started" -ForegroundColor Green
Write-Host ""

Write-Host "Step 3: Waiting for service to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test health endpoint
Write-Host "Step 4: Testing endpoints..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "http://localhost:$Port/health" -UseBasicParsing
    if ($health.Content -like '*"status":"ok"*') {
        Write-Host "✓ Health check passed" -ForegroundColor Green
    } else {
        throw "Health check failed"
    }
} catch {
    Write-Host "✗ Health check failed" -ForegroundColor Red
    docker logs $ImageName
    exit 1
}

# Test search endpoint
Write-Host "Testing search endpoint..." -ForegroundColor Yellow
try {
    $search = Invoke-WebRequest -Uri "http://localhost:$Port/search?q=python&limit=1&engine=duckduckgo" -UseBasicParsing
    if ($search.Content -like '*python*') {
        Write-Host "✓ Search endpoint working" -ForegroundColor Green
    } else {
        throw "Search endpoint failed"
    }
} catch {
    Write-Host "✗ Search endpoint failed" -ForegroundColor Red
    docker logs $ImageName
    exit 1
}

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "All tests passed!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Service is running at: http://localhost:$Port"
Write-Host "  Health: http://localhost:$Port/health"
Write-Host "  Docs: http://localhost:$Port/docs"
Write-Host "  Search: http://localhost:$Port/search?q=test&limit=5&engine=duckduckgo"
Write-Host ""
Write-Host "View logs: docker logs $ImageName"
Write-Host "Stop container: docker stop $ImageName"
Write-Host ""
Write-Host "Ready for Cloud Run deployment!" -ForegroundColor Green
