#!/bin/bash
# Development environment startup script

echo "Starting Task Management System in Development Mode..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

# Parse command line arguments
DETACHED=false
MONITORING=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--detached)
            DETACHED=true
            shift
            ;;
        --monitoring)
            MONITORING=true
            shift
            ;;
        --help)
            echo "Usage: $0 [-d|--detached] [--monitoring] [--help]"
            echo "  -d, --detached  Run in detached mode (background)"
            echo "  --monitoring    Start with monitoring stack (Prometheus, Grafana, Fluentd)"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build compose command
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.dev.yml"
if [ "$MONITORING" = true ]; then
    COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.monitoring.yml"
    echo "Starting with monitoring stack enabled..."
fi

# Start development environment
if [ "$DETACHED" = true ]; then
    docker-compose $COMPOSE_FILES up -d --build
    echo "Development environment started in detached mode!"
else
    docker-compose $COMPOSE_FILES up --build
fi

echo "Development environment started!"
echo ""
echo "Application Services:"
echo "Frontend: http://localhost:3000"
echo "User Service: http://localhost:8001"
echo "Task Service: http://localhost:8002"
echo "Notification Service: http://localhost:8003"
echo ""
echo "Database Services:"
echo "PostgreSQL: localhost:5432"
echo "MongoDB: localhost:27017"

if [ "$MONITORING" = true ]; then
    echo ""
    echo "Monitoring Services:"
    echo "Prometheus: http://localhost:9090"
    echo "Grafana: http://localhost:3001 (admin/admin123)"
    echo "cAdvisor: http://localhost:8080"
    echo "Node Exporter: http://localhost:9100"
fi

echo ""
echo "Health Checks:"
echo "User Service Health: http://localhost:8001/health"
echo "Task Service Health: http://localhost:8002/health"
echo "Notification Service Health: http://localhost:8003/health"

if [ "$DETACHED" = true ]; then
    echo ""
    echo "To view logs: docker-compose $COMPOSE_FILES logs -f [service_name]"
    echo "To stop: docker-compose $COMPOSE_FILES down"
fi