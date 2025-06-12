#!/usr/bin/env pwsh

# Navigate to the directory containing docker-compose.yml (if not already there)
# Set-Location -Path "/path/to/your/project"
$ComposeFile = "docker-compose.yml"

# Stop existing containers
Write-Host "Stopping existing containers..."
docker compose -f $ComposeFile down

# Build and start services
Write-Host "Building and starting services..."
docker compose -f $ComposeFile up -d --build

Write-Host "Waiting a few seconds before fetching logs..."
Start-Sleep -Seconds 5

# Show logs
Write-Host "Recent logs:"
docker compose -f $ComposeFile logs --tail=20

Write-Host ""
Write-Host "Deployment completed!"
Write-Host ""
Write-Host "Useful commands:"
Write-Host "  View logs: docker compose -f $ComposeFile logs -f"
Write-Host "  Stop: docker compose -f $ComposeFile down"
Write-Host "  Restart: docker compose -f $ComposeFile restart"
Write-Host ""