#!/bin/bash

# Quick test runner for local development
# This script runs tests for a specific service or all services quickly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_usage() {
    echo "Usage: $0 [service] [options]"
    echo ""
    echo "Services:"
    echo "  user          Run user service tests"
    echo "  task          Run task service tests"
    echo "  notification  Run notification service tests"
    echo "  frontend      Run frontend tests"
    echo "  all           Run all service tests (default)"
    echo ""
    echo "Options:"
    echo "  --watch       Run tests in watch mode"
    echo "  --coverage    Run with coverage reporting"
    echo "  --verbose     Run with verbose output"
    echo "  --help        Show this help message"
}

# Default values
SERVICE="all"
WATCH_MODE=false
COVERAGE=false
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        user|task|notification|frontend|all)
            SERVICE="$1"
            shift
            ;;
        --watch)
            WATCH_MODE=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            print_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# Function to run Python service tests
run_python_tests() {
    local service_name=$1
    local service_dir=$2
    
    echo -e "${BLUE}Running $service_name tests...${NC}"
    
    cd $service_dir
    
    # Build pytest command
    local pytest_cmd="pytest tests/"
    
    if [ "$VERBOSE" = true ]; then
        pytest_cmd="$pytest_cmd -v"
    fi
    
    if [ "$COVERAGE" = true ]; then
        pytest_cmd="$pytest_cmd --cov=app --cov-report=term-missing"
    fi
    
    if [ "$WATCH_MODE" = true ]; then
        pytest_cmd="$pytest_cmd --looponfail"
    fi
    
    # Run tests
    if eval $pytest_cmd; then
        echo -e "${GREEN}✓ $service_name tests passed${NC}"
    else
        echo -e "${RED}✗ $service_name tests failed${NC}"
        cd ..
        exit 1
    fi
    
    cd ..
}

# Function to run frontend tests
run_frontend_tests() {
    echo -e "${BLUE}Running frontend tests...${NC}"
    
    cd frontend
    
    # Build npm test command
    local npm_cmd="npm run test"
    
    if [ "$WATCH_MODE" = true ]; then
        npm_cmd="npm run test:watch"
    elif [ "$COVERAGE" = true ]; then
        npm_cmd="npm run test:coverage"
    fi
    
    # Run tests
    if eval $npm_cmd; then
        echo -e "${GREEN}✓ Frontend tests passed${NC}"
    else
        echo -e "${RED}✗ Frontend tests failed${NC}"
        cd ..
        exit 1
    fi
    
    cd ..
}

# Main execution
echo -e "${BLUE}=== Quick Test Runner ===${NC}"

case $SERVICE in
    "user")
        run_python_tests "User Service" "user-service"
        ;;
    "task")
        run_python_tests "Task Service" "task-service"
        ;;
    "notification")
        run_python_tests "Notification Service" "notification-service"
        ;;
    "frontend")
        run_frontend_tests
        ;;
    "all")
        run_python_tests "User Service" "user-service"
        run_python_tests "Task Service" "task-service"
        run_python_tests "Notification Service" "notification-service"
        run_frontend_tests
        ;;
esac

echo -e "\n${GREEN}🎉 All selected tests completed successfully!${NC}"