# Test Runner Script for Microservices Task Management System
# This script runs all tests across all services with coverage reporting

param(
    [string]$Target = "all",
    [int]$CoverageThreshold = 80
)

# Configuration
$TestResultsDir = "test-results"
$CoverageDir = "coverage-reports"

# Create directories
New-Item -ItemType Directory -Force -Path $TestResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path $CoverageDir | Out-Null

Write-Host "=== Microservices Task Management Test Suite ===" -ForegroundColor Blue
Write-Host "Starting comprehensive test execution..."

# Function to print section headers
function Write-Section {
    param([string]$Title)
    Write-Host "`n=== $Title ===" -ForegroundColor Blue
}

# Function to run service tests with coverage
function Invoke-ServiceTests {
    param(
        [string]$ServiceName,
        [string]$ServiceDir
    )
    
    Write-Section "Testing $ServiceName"
    
    Push-Location $ServiceDir
    
    try {
        # Install dependencies if needed
        if (Test-Path "requirements.txt") {
            Write-Host "Installing Python dependencies..."
            pip install -r requirements.txt *>$null
            pip install pytest-cov pytest-html *>$null
        }
        
        # Run tests with coverage
        Write-Host "Running unit tests with coverage..."
        $result = pytest tests/ `
            --cov=app `
            --cov-report=html:../$CoverageDir/$ServiceName-coverage `
            --cov-report=xml:../$CoverageDir/$ServiceName-coverage.xml `
            --cov-report=term-missing `
            --cov-fail-under=$CoverageThreshold `
            --html=../$TestResultsDir/$ServiceName-report.html `
            --self-contained-html `
            --junitxml=../$TestResultsDir/$ServiceName-junit.xml `
            -v
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ $ServiceName tests passed" -ForegroundColor Green
            return $true
        } else {
            Write-Host "✗ $ServiceName tests failed" -ForegroundColor Red
            return $false
        }
    }
    finally {
        Pop-Location
    }
}

# Function to run frontend tests
function Invoke-FrontendTests {
    Write-Section "Testing Frontend"
    
    Push-Location frontend
    
    try {
        # Install dependencies
        Write-Host "Installing Node.js dependencies..."
        npm ci *>$null
        
        # Run tests with coverage
        Write-Host "Running frontend tests with coverage..."
        npm run test -- --coverage --reporter=junit --outputFile=../$TestResultsDir/frontend-junit.xml
        
        # Move coverage reports
        if (Test-Path "coverage") {
            Move-Item coverage ../$CoverageDir/frontend-coverage -Force
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Frontend tests passed" -ForegroundColor Green
            return $true
        } else {
            Write-Host "✗ Frontend tests failed" -ForegroundColor Red
            return $false
        }
    }
    finally {
        Pop-Location
    }
}

# Function to run integration tests
function Invoke-IntegrationTests {
    Write-Section "Integration Tests"
    
    try {
        Write-Host "Starting services for integration tests..."
        docker-compose -f docker-compose.test.yml up -d --build
        
        # Wait for services to be ready
        Write-Host "Waiting for services to be ready..."
        Start-Sleep 30
        
        # Run integration tests
        Write-Host "Running integration tests..."
        Push-Location tests/integration
        
        python -m pytest . `
            --html=../../$TestResultsDir/integration-report.html `
            --self-contained-html `
            --junitxml=../../$TestResultsDir/integration-junit.xml `
            -v
        
        $testResult = $LASTEXITCODE -eq 0
        Pop-Location
        
        if ($testResult) {
            Write-Host "✓ Integration tests passed" -ForegroundColor Green
        } else {
            Write-Host "✗ Integration tests failed" -ForegroundColor Red
        }
        
        return $testResult
    }
    finally {
        # Stop test services
        Write-Host "Stopping test services..."
        docker-compose -f docker-compose.test.yml down -v
    }
}

# Main execution
function Invoke-AllTests {
    $overallSuccess = $true
    
    # Run service tests
    $overallSuccess = (Invoke-ServiceTests "User Service" "user-service") -and $overallSuccess
    $overallSuccess = (Invoke-ServiceTests "Task Service" "task-service") -and $overallSuccess
    $overallSuccess = (Invoke-ServiceTests "Notification Service" "notification-service") -and $overallSuccess
    
    # Run frontend tests
    $overallSuccess = (Invoke-FrontendTests) -and $overallSuccess
    
    # Run integration tests
    $overallSuccess = (Invoke-IntegrationTests) -and $overallSuccess
    
    # Generate summary
    Write-Section "Coverage Summary"
    Write-Host "Coverage reports generated in: $CoverageDir/"
    Write-Host "Test reports generated in: $TestResultsDir/"
    
    if ($overallSuccess) {
        Write-Host "`n🎉 All tests passed successfully!" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "`n❌ Some tests failed. Check the reports for details." -ForegroundColor Red
        exit 1
    }
}

# Parse target and execute
switch ($Target.ToLower()) {
    "user" { 
        $success = Invoke-ServiceTests "User Service" "user-service"
        exit $(if ($success) { 0 } else { 1 })
    }
    "task" { 
        $success = Invoke-ServiceTests "Task Service" "task-service"
        exit $(if ($success) { 0 } else { 1 })
    }
    "notification" { 
        $success = Invoke-ServiceTests "Notification Service" "notification-service"
        exit $(if ($success) { 0 } else { 1 })
    }
    "frontend" { 
        $success = Invoke-FrontendTests
        exit $(if ($success) { 0 } else { 1 })
    }
    "integration" { 
        $success = Invoke-IntegrationTests
        exit $(if ($success) { 0 } else { 1 })
    }
    default { 
        Invoke-AllTests
    }
}