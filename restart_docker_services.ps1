#!/usr/bin/env pwsh

# Navigate to the directory containing docker-compose.yml (if not already there)
# Set-Location -Path "/path/to/your/project"

Write-Host "Stopping existing Docker Compose services..."
docker-compose down

Write-Host "Starting Docker Compose services..."
docker-compose up -d

Write-Host "Docker Compose services restarted successfully."

Write-Host "Waiting a few seconds before fetching logs..."
Start-Sleep -Seconds 5

Write-Host "Fetching Docker Compose logs..."
docker-compose logs -f 