# Google Cloud Run Deployment Script (PowerShell)
# This script automates the deployment of Scrapling Search API to Cloud Run

param(
    [string]$Region = "us-central1",
    [string]$Memory = "1Gi",
    [int]$Cpu = 1,
    [int]$Timeout = 60,
    [int]$MaxInstances = 10,
    [int]$MinInstances = 0,
    [switch]$SkipConfirmation
)

$ErrorActionPreference = "Stop"

# Configuration
$ServiceName = "scrapling-search-api"

Write-Host "================================" -ForegroundColor Green
Write-Host "Cloud Run Deployment Script" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# Check if gcloud is installed
try {
    $null = Get-Command gcloud -ErrorAction Stop
} catch {
    Write-Host "Error: gcloud CLI is not installed" -ForegroundColor Red
    Write-Host "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
}

# Get project ID
$ProjectId = gcloud config get-value project 2>$null
if ([string]::IsNullOrEmpty($ProjectId)) {
    Write-Host "Error: No GCP project configured" -ForegroundColor Red
    Write-Host "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
}

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Project ID: $ProjectId"
Write-Host "  Service Name: $ServiceName"
Write-Host "  Region: $Region"
Write-Host "  Memory: $Memory"
Write-Host "  CPU: $Cpu"
Write-Host "  Timeout: ${Timeout}s"
Write-Host "  Min Instances: $MinInstances"
Write-Host "  Max Instances: $MaxInstances"
Write-Host ""

# Confirmation
if (-not $SkipConfirmation) {
    $confirmation = Read-Host "Deploy to Cloud Run? (y/N)"
    if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
        Write-Host "Deployment cancelled"
        exit 0
    }
}

Write-Host ""
Write-Host "Step 1: Enabling required APIs..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com --project=$ProjectId
gcloud services enable cloudbuild.googleapis.com --project=$ProjectId
Write-Host "✓ APIs enabled" -ForegroundColor Green

Write-Host ""
Write-Host "Step 2: Building and deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $ServiceName `
    --source . `
    --platform managed `
    --region $Region `
    --allow-unauthenticated `
    --memory $Memory `
    --cpu $Cpu `
    --timeout $Timeout `
    --max-instances $MaxInstances `
    --min-instances $MinInstances `
    --project $ProjectId

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

# Get service URL
$ServiceUrl = gcloud run services describe $ServiceName --region $Region --format='value(status.url)' --project=$ProjectId 2>$null

if (-not [string]::IsNullOrEmpty($ServiceUrl)) {
    Write-Host ""
    Write-Host "Service URL: $ServiceUrl" -ForegroundColor Green
    Write-Host ""
    Write-Host "Test endpoints:"
    Write-Host "  Health: $ServiceUrl/health"
    Write-Host "  Docs: $ServiceUrl/docs"
    Write-Host ("  Example: " + $ServiceUrl + '/search?q=python&limit=5&engine=duckduckgo')
    Write-Host ""
    
    # Test health endpoint
    Write-Host "Testing health endpoint..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5  # Wait for deployment to stabilize
    try {
        $response = Invoke-WebRequest -Uri "${ServiceUrl}/health" -UseBasicParsing
        if ($response.Content -like '*"status":"ok"*') {
            Write-Host "✓ Service is healthy!" -ForegroundColor Green
        } else {
            Write-Host "✗ Health check failed" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ Health check failed: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  View logs: gcloud run services logs read $ServiceName --region $Region --project $ProjectId"
Write-Host "  Get URL: gcloud run services describe $ServiceName --region $Region --format='value(status.url)' --project $ProjectId"
Write-Host "  Delete: gcloud run services delete $ServiceName --region $Region --project $ProjectId"
