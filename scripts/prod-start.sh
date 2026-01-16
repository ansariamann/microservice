#!/bin/bash
# Production environment startup script

echo "Starting Task Management System in Production Mode..."

# Check if .env.prod file exists
if [ ! -f .env.prod ]; then
    echo "Error: .env.prod file not found. Please create it with production configuration."
    exit 1
fi

# Use production environment file
export $(cat .env.prod | xargs)

# Parse command line arguments
MONITORING=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --monitoring)
            MONITORING=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--monitoring] [--help]"
            echo "  --monitoring  Start with monitoring stack (Prometheus, Grafana, Fluentd)"
            echo "  --help        Show this help message"
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
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
if [ "$MONITORING" = true ]; then
    COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.monitoring.yml"
    echo "Starting with monitoring stack enabled..."
fi

# Start production environment
docker-compose $COMPOSE_FILES up -d --build

echo "Production environment started!"
echo "Application: http://localhost"
echo "API Gateway: http://localhost"

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
echo "Application Health: http://localhost/health"
echo "Nginx Status: http://localhost/nginx_status"

# Show running containers
docker-compose $COMPOSE_FILES ps

echo ""
echo "To view logs: docker-compose $COMPOSE_FILES logs -f [service_name]"
echo "To stop: docker-compose $COMPOSE_FILES down"