#!/bin/bash

# Test Runner Script for Microservices Task Management System
# This script runs all tests across all services with coverage reporting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COVERAGE_THRESHOLD=80
TEST_RESULTS_DIR="test-results"
COVERAGE_DIR="coverage-reports"

# Create directories
mkdir -p $TEST_RESULTS_DIR
mkdir -p $COVERAGE_DIR

echo -e "${BLUE}=== Microservices Task Management Test Suite ===${NC}"
echo "Starting comprehensive test execution..."

# Function to print section headers
print_section() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Function to run service tests with coverage
run_service_tests() {
    local service_name=$1
    local service_dir=$2
    
    print_section "Testing $service_name"
    
    cd $service_dir
    
    # Install dependencies if needed
    if [ -f "requirements.txt" ]; then
        echo "Installing Python dependencies..."
        pip install -r requirements.txt > /dev/null 2>&1
        pip install pytest-cov pytest-html > /dev/null 2>&1
    fi
    
    # Run tests with coverage
    echo "Running unit tests with coverage..."
    pytest tests/ \
        --cov=app \
        --cov-report=html:../$COVERAGE_DIR/$service_name-coverage \
        --cov-report=xml:../$COVERAGE_DIR/$service_name-coverage.xml \
        --cov-report=term-missing \
        --cov-fail-under=$COVERAGE_THRESHOLD \
        --html=../$TEST_RESULTS_DIR/$service_name-report.html \
        --self-contained-html \
        --junitxml=../$TEST_RESULTS_DIR/$service_name-junit.xml \
        -v
    
    local exit_code=$?
    cd ..
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✓ $service_name tests passed${NC}"
    else
        echo -e "${RED}✗ $service_name tests failed${NC}"
        return $exit_code
    fi
}

# Function to run frontend tests
run_frontend_tests() {
    print_section "Testing Frontend"
    
    cd frontend
    
    # Install dependencies
    echo "Installing Node.js dependencies..."
    npm ci > /dev/null 2>&1
    
    # Run tests with coverage
    echo "Running frontend tests with coverage..."
    npm run test -- --coverage --reporter=junit --outputFile=../$TEST_RESULTS_DIR/frontend-junit.xml
    
    # Move coverage reports
    if [ -d "coverage" ]; then
        mv coverage ../$COVERAGE_DIR/frontend-coverage
    fi
    
    local exit_code=$?
    cd ..
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✓ Frontend tests passed${NC}"
    else
        echo -e "${RED}✗ Frontend tests failed${NC}"
        return $exit_code
    fi
}

# Function to run integration tests
run_integration_tests() {
    print_section "Integration Tests"
    
    echo "Starting services for integration tests..."
    docker-compose -f docker-compose.test.yml up -d --build
    
    # Wait for services to be ready
    echo "Waiting for services to be ready..."
    sleep 30
    
    # Run integration tests
    echo "Running integration tests..."
    cd tests/integration
    python -m pytest . \
        --html=../../$TEST_RESULTS_DIR/integration-report.html \
        --self-contained-html \
        --junitxml=../../$TEST_RESULTS_DIR/integration-junit.xml \
        -v
    
    local exit_code=$?
    cd ../..
    
    # Stop test services
    echo "Stopping test services..."
    docker-compose -f docker-compose.test.yml down -v
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✓ Integration tests passed${NC}"
    else
        echo -e "${RED}✗ Integration tests failed${NC}"
        return $exit_code
    fi
}

# Main execution
main() {
    local overall_exit_code=0
    
    # Run service tests
    run_service_tests "User Service" "user-service" || overall_exit_code=1
    run_service_tests "Task Service" "task-service" || overall_exit_code=1
    run_service_tests "Notification Service" "notification-service" || overall_exit_code=1
    
    # Run frontend tests
    run_frontend_tests || overall_exit_code=1
    
    # Run integration tests
    run_integration_tests || overall_exit_code=1
    
    # Generate combined coverage report
    print_section "Coverage Summary"
    echo "Coverage reports generated in: $COVERAGE_DIR/"
    echo "Test reports generated in: $TEST_RESULTS_DIR/"
    
    if [ $overall_exit_code -eq 0 ]; then
        echo -e "\n${GREEN}🎉 All tests passed successfully!${NC}"
    else
        echo -e "\n${RED}❌ Some tests failed. Check the reports for details.${NC}"
    fi
    
    return $overall_exit_code
}

# Parse command line arguments
case "${1:-all}" in
    "user")
        run_service_tests "User Service" "user-service"
        ;;
    "task")
        run_service_tests "Task Service" "task-service"
        ;;
    "notification")
        run_service_tests "Notification Service" "notification-service"
        ;;
    "frontend")
        run_frontend_tests
        ;;
    "integration")
        run_integration_tests
        ;;
    "all"|*)
        main
        ;;
esac