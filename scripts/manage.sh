#!/bin/bash
# Task Management System - Deployment Management Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Show usage information
show_usage() {
    echo "Task Management System - Deployment Management"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  dev [--monitoring] [--detached]  Start development environment"
    echo "  prod [--monitoring]              Start production environment"
    echo "  stop [dev|prod]                  Stop environment"
    echo "  logs [service_name]              View logs"
    echo "  status                           Show container status"
    echo "  health                           Check service health"
    echo "  clean                            Clean up containers and volumes"
    echo "  setup                            Initial setup and configuration"
    echo ""
    echo "Options:"
    echo "  --monitoring    Include monitoring stack (Prometheus, Grafana, etc.)"
    echo "  --detached      Run in detached mode (development only)"
    echo ""
    echo "Examples:"
    echo "  $0 dev --monitoring              # Start dev with monitoring"
    echo "  $0 prod                          # Start production"
    echo "  $0 logs user-service             # View user service logs"
    echo "  $0 stop dev                      # Stop development environment"
}

# Check if required files exist
check_prerequisites() {
    local env_file="$1"
    
    if [ ! -f "$PROJECT_ROOT/$env_file" ]; then
        print_error "$env_file file not found!"
        if [ "$env_file" = ".env" ]; then
            print_info "Please copy .env.example to .env and configure it."
        else
            print_info "Please create $env_file with production configuration."
        fi
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed!"
        exit 1
    fi
}

# Start development environment
start_dev() {
    local monitoring=false
    local detached=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --monitoring)
                monitoring=true
                shift
                ;;
            --detached)
                detached=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    check_prerequisites ".env"
    
    print_info "Starting development environment..."
    
    # Build compose command
    local compose_files="-f docker-compose.yml -f docker-compose.dev.yml"
    if [ "$monitoring" = true ]; then
        compose_files="$compose_files -f docker-compose.monitoring.yml"
        print_info "Including monitoring stack..."
    fi
    
    cd "$PROJECT_ROOT"
    
    if [ "$detached" = true ]; then
        docker-compose $compose_files up -d --build
        print_success "Development environment started in detached mode!"
    else
        docker-compose $compose_files up --build
    fi
}

# Start production environment
start_prod() {
    local monitoring=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --monitoring)
                monitoring=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    check_prerequisites ".env.prod"
    
    print_info "Starting production environment..."
    
    # Build compose command
    local compose_files="-f docker-compose.yml -f docker-compose.prod.yml"
    if [ "$monitoring" = true ]; then
        compose_files="$compose_files -f docker-compose.monitoring.yml"
        print_info "Including monitoring stack..."
    fi
    
    cd "$PROJECT_ROOT"
    
    # Export production environment variables
    export $(cat .env.prod | xargs)
    
    docker-compose $compose_files up -d --build
    
    print_success "Production environment started!"
    print_info "Application: http://localhost"
    
    if [ "$monitoring" = true ]; then
        echo ""
        print_info "Monitoring Services:"
        echo "  Prometheus: http://localhost:9090"
        echo "  Grafana: http://localhost:3001 (admin/admin123)"
        echo "  cAdvisor: http://localhost:8080"
        echo "  Node Exporter: http://localhost:9100"
    fi
}

# Stop environment
stop_env() {
    local env_type="$1"
    
    cd "$PROJECT_ROOT"
    
    case $env_type in
        dev)
            print_info "Stopping development environment..."
            docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.monitoring.yml down
            ;;
        prod)
            print_info "Stopping production environment..."
            docker-compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.monitoring.yml down
            ;;
        *)
            print_info "Stopping all environments..."
            docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.monitoring.yml down 2>/dev/null || true
            docker-compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.monitoring.yml down 2>/dev/null || true
            ;;
    esac
    
    print_success "Environment stopped!"
}

# View logs
view_logs() {
    local service="$1"
    
    cd "$PROJECT_ROOT"
    
    if [ -n "$service" ]; then
        print_info "Viewing logs for $service..."
        docker-compose logs -f "$service"
    else
        print_info "Viewing all logs..."
        docker-compose logs -f
    fi
}

# Show container status
show_status() {
    cd "$PROJECT_ROOT"
    
    print_info "Container Status:"
    docker-compose ps
    
    echo ""
    print_info "Docker System Info:"
    docker system df
}

# Check service health
check_health() {
    cd "$PROJECT_ROOT"
    
    print_info "Checking service health..."
    
    local services=("user-service:8001" "task-service:8002" "notification-service:8003")
    
    for service in "${services[@]}"; do
        local name=$(echo $service | cut -d: -f1)
        local port=$(echo $service | cut -d: -f2)
        
        if curl -f -s "http://localhost:$port/health" > /dev/null; then
            print_success "$name is healthy"
        else
            print_error "$name is not responding"
        fi
    done
    
    # Check nginx if running
    if curl -f -s "http://localhost/health" > /dev/null; then
        print_success "nginx gateway is healthy"
    else
        print_warning "nginx gateway is not responding (may not be running in dev mode)"
    fi
}

# Clean up containers and volumes
clean_up() {
    cd "$PROJECT_ROOT"
    
    print_warning "This will remove all containers, networks, and volumes!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cleaning up..."
        
        # Stop all services
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.monitoring.yml down -v 2>/dev/null || true
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.monitoring.yml down -v 2>/dev/null || true
        
        # Remove unused containers, networks, images
        docker system prune -f
        
        print_success "Cleanup completed!"
    else
        print_info "Cleanup cancelled."
    fi
}

# Initial setup
setup() {
    print_info "Setting up Task Management System..."
    
    # Check if .env exists
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            print_success "Created .env from .env.example"
        else
            print_warning ".env.example not found, creating basic .env file"
            # Create basic .env file
            cat > "$PROJECT_ROOT/.env" << EOF
# Docker Compose Environment Variables
JWT_SECRET=change-this-secret-key-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Database Configuration
POSTGRES_DB=userdb
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_PORT=5432

MONGODB_DATABASE=taskdb
MONGODB_PORT=27017

# Service Ports
USER_SERVICE_PORT=8001
TASK_SERVICE_PORT=8002
NOTIFICATION_SERVICE_PORT=8003
FRONTEND_PORT=3000

# Debug Mode
DEBUG=true

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Frontend API URLs
REACT_APP_API_BASE_URL=http://localhost:8080
REACT_APP_USER_SERVICE_URL=http://localhost:8001
REACT_APP_TASK_SERVICE_URL=http://localhost:8002
REACT_APP_NOTIFICATION_SERVICE_URL=http://localhost:8003
EOF
        fi
    fi
    
    # Check if .env.prod exists
    if [ ! -f "$PROJECT_ROOT/.env.prod" ]; then
        print_info "Creating .env.prod template..."
        cat > "$PROJECT_ROOT/.env.prod" << EOF
# Production Environment Variables
JWT_SECRET=CHANGE-THIS-SECRET-KEY-IN-PRODUCTION-USE-STRONG-RANDOM-STRING
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Database Configuration
POSTGRES_DB=userdb_prod
POSTGRES_USER=user
POSTGRES_PASSWORD=CHANGE-THIS-PASSWORD-IN-PRODUCTION
POSTGRES_PORT=5432

MONGODB_DATABASE=taskdb_prod
MONGODB_PORT=27017

# Service Ports (internal only in production)
USER_SERVICE_PORT=8001
TASK_SERVICE_PORT=8002
NOTIFICATION_SERVICE_PORT=8003
FRONTEND_PORT=3000

# Production Mode
DEBUG=false

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# CORS Configuration
ALLOWED_ORIGINS=http://localhost,https://yourdomain.com

# Frontend API URLs (through nginx)
REACT_APP_API_BASE_URL=http://localhost
REACT_APP_USER_SERVICE_URL=http://localhost
REACT_APP_TASK_SERVICE_URL=http://localhost
REACT_APP_NOTIFICATION_SERVICE_URL=http://localhost
EOF
        print_success "Created .env.prod template"
        print_warning "Please update .env.prod with secure values before production deployment!"
    fi
    
    # Make scripts executable
    chmod +x "$PROJECT_ROOT/scripts/"*.sh
    
    print_success "Setup completed!"
    print_info "You can now run: $0 dev"
}

# Main command handling
case "${1:-}" in
    dev)
        shift
        start_dev "$@"
        ;;
    prod)
        shift
        start_prod "$@"
        ;;
    stop)
        stop_env "$2"
        ;;
    logs)
        view_logs "$2"
        ;;
    status)
        show_status
        ;;
    health)
        check_health
        ;;
    clean)
        clean_up
        ;;
    setup)
        setup
        ;;
    --help|help|"")
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac