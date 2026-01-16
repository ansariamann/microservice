# Microservices Task Management System

A distributed task management system built with microservices architecture, featuring user authentication, task management, and real-time notifications.

## 🏗️ Architecture

The system consists of four main components:

- **User Service** (FastAPI + PostgreSQL) - User registration, authentication, and profile management
- **Task Service** (FastAPI + MongoDB) - Task CRUD operations and assignment management
- **Notification Service** (FastAPI + SQLite) - Notification creation and retrieval
- **Frontend** (React + TypeScript) - Web interface for user interaction

### System Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  Nginx Gateway  │
│   (Port 3000)    │    │   (Port 80)     │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌───▼────┐ ┌────▼──────┐
│ User Service │ │ Task   │ │Notification│
│ (Port 8001)  │ │Service │ │  Service  │
│              │ │(8002)  │ │  (8003)   │
└───────┬──────┘ └───┬────┘ └────┬──────┘
        │            │           │
┌───────▼──────┐ ┌───▼────┐ ┌────▼──────┐
│ PostgreSQL   │ │MongoDB │ │  SQLite   │
│ (Port 5432)  │ │(27017) │ │   (File)  │
└──────────────┘ └────────┘ └───────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **Git** for cloning the repository
- **4GB RAM** minimum for running all services

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd microservices-task-management

# Run initial setup (creates environment files)
./scripts/manage.sh setup
```

### 2. Configure Environment

Update the generated `.env` file with your settings:

```bash
# Edit development configuration
nano .env

# Key settings to update:
# JWT_SECRET=your-secret-key-here
# POSTGRES_PASSWORD=your-secure-password
```

### 3. Start the System

```bash
# Start development environment
./scripts/manage.sh dev

# Or start with monitoring stack
./scripts/manage.sh dev --monitoring

# Or start in background
./scripts/manage.sh dev --detached
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **API Documentation**:
  - User Service: http://localhost:8001/docs
  - Task Service: http://localhost:8002/docs
  - Notification Service: http://localhost:8003/docs

### 5. Test the System

```bash
# Check service health
./scripts/manage.sh health

# View logs
./scripts/manage.sh logs

# Run tests
./scripts/run-tests.sh
```

## 📁 Project Structure

```
microservices-task-management/
├── user-service/              # User authentication and profile service
│   ├── app/                  # FastAPI application code
│   │   ├── main.py          # API endpoints and application setup
│   │   ├── models.py        # SQLAlchemy models and schemas
│   │   ├── database.py      # Database connection and configuration
│   │   ├── auth.py          # JWT authentication logic
│   │   └── services.py      # Business logic layer
│   ├── tests/               # Unit and integration tests
│   ├── Dockerfile           # Container configuration
│   ├── requirements.txt     # Python dependencies
│   ├── .env.template        # Environment variables template
│   └── API_DOCUMENTATION.md # Detailed API documentation
├── task-service/             # Task management service
│   ├── app/                 # FastAPI application code
│   │   ├── main.py         # API endpoints and application setup
│   │   ├── models.py       # MongoDB document models
│   │   ├── database.py     # MongoDB connection and configuration
│   │   ├── services.py     # Business logic layer
│   │   └── notification_client.py # Service-to-service communication
│   ├── tests/              # Unit and integration tests
│   ├── Dockerfile          # Container configuration
│   ├── requirements.txt    # Python dependencies
│   ├── .env.template       # Environment variables template
│   └── API_DOCUMENTATION.md # Detailed API documentation
├── notification-service/     # Notification service
│   ├── app/                 # FastAPI application code
│   │   ├── main.py         # API endpoints and application setup
│   │   ├── models.py       # SQLAlchemy models for SQLite
│   │   ├── database.py     # SQLite connection and configuration
│   │   └── repository.py   # Data access layer
│   ├── tests/              # Unit and integration tests
│   ├── Dockerfile          # Container configuration
│   ├── requirements.txt    # Python dependencies
│   ├── .env.template       # Environment variables template
│   └── API_DOCUMENTATION.md # Detailed API documentation
├── frontend/                 # React frontend application
│   ├── src/                 # TypeScript/React source code
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client services
│   │   ├── contexts/       # React contexts (Auth, Notifications)
│   │   └── types/          # TypeScript type definitions
│   ├── public/             # Static assets
│   ├── Dockerfile          # Container configuration
│   ├── package.json        # Node.js dependencies
│   ├── nginx.conf          # Nginx configuration for production
│   └── vite.config.ts      # Vite build configuration
├── shared/                   # Shared utilities across services
│   ├── jwt_utils.py        # JWT token utilities
│   ├── config.py           # Common configuration
│   ├── logging_config.py   # Structured logging setup
│   ├── health_check.py     # Health check utilities
│   ├── metrics.py          # Performance metrics collection
│   └── security_middleware.py # Security and rate limiting
├── scripts/                  # Deployment and management scripts
│   ├── manage.sh           # Main management script
│   ├── dev-start.sh        # Development environment startup
│   ├── prod-start.sh       # Production environment startup
│   └── run-tests.sh        # Test execution script
├── tests/                    # System-wide integration tests
│   └── integration/        # End-to-end test suites
├── monitoring/               # Monitoring stack configuration
│   ├── prometheus/         # Prometheus configuration
│   ├── grafana/           # Grafana dashboards and config
│   └── fluentd/           # Log aggregation configuration
├── nginx/                    # API Gateway configuration
│   └── conf.d/            # Nginx virtual host configurations
├── docker-compose.yml        # Base container orchestration
├── docker-compose.dev.yml    # Development environment overrides
├── docker-compose.prod.yml   # Production environment overrides
├── docker-compose.monitoring.yml # Monitoring stack configuration
├── .env                      # Development environment variables
├── .env.prod                 # Production environment variables
└── README.md                 # This file
```

## 📚 Documentation

### Setup and Deployment Guides

- **[Development Setup Guide](docs/DEVELOPMENT_SETUP.md)** - Detailed development environment setup
- **[Production Deployment Guide](docs/PRODUCTION_DEPLOYMENT.md)** - Production deployment with security and monitoring
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### API Documentation

Each service provides comprehensive API documentation:

- **[User Service API](user-service/API_DOCUMENTATION.md)** - Authentication and user management
- **[Task Service API](task-service/API_DOCUMENTATION.md)** - Task CRUD and assignment operations
- **[Notification Service API](notification-service/API_DOCUMENTATION.md)** - Notification management

### Interactive API Documentation

- **User Service**: http://localhost:8001/docs
- **Task Service**: http://localhost:8002/docs
- **Notification Service**: http://localhost:8003/docs

## 🛠️ Development

### Development Options

**Option 1: Full Docker Development (Recommended)**

```bash
# Start all services with hot reload
./scripts/manage.sh dev

# Start with monitoring stack
./scripts/manage.sh dev --monitoring
```

**Option 2: Hybrid Development**

```bash
# Start databases only
docker-compose up -d user-db task-db

# Run services locally (requires Python 3.11+ and Node.js 18+)
cd user-service && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8001
cd task-service && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8002
cd notification-service && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8003
cd frontend && npm install && npm run dev
```

### Development Commands

```bash
# Environment management
./scripts/manage.sh dev                    # Start development environment
./scripts/manage.sh dev --monitoring       # Start with monitoring stack
./scripts/manage.sh stop dev              # Stop development environment

# Monitoring and debugging
./scripts/manage.sh status                 # Show container status
./scripts/manage.sh health                 # Check service health
./scripts/manage.sh logs                   # View all logs
./scripts/manage.sh logs user-service      # View specific service logs

# Testing
./scripts/run-tests.sh                     # Run all tests
./scripts/run-tests.sh --coverage         # Run tests with coverage

# Cleanup
./scripts/manage.sh clean                  # Remove containers and volumes
```

## API Documentation

Each service provides OpenAPI/Swagger documentation:

- User Service: http://localhost:8001/docs
- Task Service: http://localhost:8002/docs
- Notification Service: http://localhost:8003/docs

## Testing

Run tests for each service:

```bash
# Backend services
cd user-service && python -m pytest
cd task-service && python -m pytest
cd notification-service && python -m pytest

# Frontend
cd frontend && npm test
```

## Security

- JWT tokens for stateless authentication
- Password hashing with bcrypt
- Input validation and sanitization
- CORS configuration for cross-origin requests
- Non-root user execution in containers

## Monitoring and Health Checks

All services include health check endpoints:

- User Service: GET /health
- Task Service: GET /health
- Notification Service: GET /health

Docker containers are configured with health checks for proper orchestration.

## Deployment

The system supports both development and production deployment configurations with comprehensive monitoring and logging capabilities.

### Development Environment

Start the development environment with hot reload and exposed database ports:

```bash
# Basic development setup
./scripts/dev-start.sh

# With monitoring stack
./scripts/dev-start.sh --monitoring

# In detached mode
./scripts/dev-start.sh --detached
```

**Development Features:**

- Hot reload for all services
- Exposed database ports for debugging
- Debug logging enabled
- Source code mounted as volumes
- Separate development databases

### Production Environment

Start the production environment with API Gateway and security hardening:

```bash
# Basic production setup
./scripts/prod-start.sh

# With monitoring stack
./scripts/prod-start.sh --monitoring
```

**Production Features:**

- Nginx API Gateway with load balancing
- No exposed service ports (access through gateway only)
- Production databases with optimized settings
- Resource limits and restart policies
- Structured JSON logging
- Health checks and monitoring endpoints

### Environment Files

- **`.env`** - Development configuration
- **`.env.prod`** - Production configuration (create from template)

**Important:** Update the following in production:

- `JWT_SECRET` - Use a strong, random secret key
- `POSTGRES_PASSWORD` - Use a secure database password
- `ALLOWED_ORIGINS` - Set to your actual domain

### Docker Compose Files

- **`docker-compose.yml`** - Base configuration
- **`docker-compose.dev.yml`** - Development overrides
- **`docker-compose.prod.yml`** - Production overrides
- **`docker-compose.monitoring.yml`** - Monitoring stack

### Monitoring and Logging

When started with `--monitoring`, the system includes:

- **Prometheus** (http://localhost:9090) - Metrics collection
- **Grafana** (http://localhost:3001) - Metrics visualization (admin/admin123)
- **Fluentd** - Log aggregation and processing
- **cAdvisor** (http://localhost:8080) - Container metrics
- **Node Exporter** (http://localhost:9100) - System metrics

### Health Checks

All services include comprehensive health checks:

- **Application Health**: `http://localhost/health`
- **Nginx Status**: `http://localhost/nginx_status`
- **Individual Services**: `http://localhost:800X/health`

### Logging Configuration

**Development:**

- Pretty formatted logs
- DEBUG level logging
- Console output

**Production:**

- Structured JSON logs
- INFO level logging
- Log rotation (10MB, 5 files)
- Service and environment labels

### Resource Management

**Production Resource Limits:**

- **Databases**: 1 CPU, 1GB RAM
- **Backend Services**: 0.5 CPU, 512MB RAM (2 replicas each)
- **Frontend**: 0.5 CPU, 512MB RAM (2 replicas)
- **Nginx**: 0.5 CPU, 256MB RAM

### Security Hardening

**Production Security Features:**

- No exposed service ports (Nginx gateway only)
- Rate limiting on API endpoints
- Security headers (X-Frame-Options, X-Content-Type-Options, etc.)
- Non-root container execution
- Network isolation
- Input validation and sanitization

### Backup and Data Persistence

**Data Volumes:**

- `user_db_prod_data` - PostgreSQL user data
- `task_db_prod_data` - MongoDB task data
- `notification_prod_data` - SQLite notification data
- `nginx_logs` - Nginx access and error logs

### Troubleshooting

**View Logs:**

```bash
# All services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f user-service
```

**Check Service Health:**

```bash
# Container status
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Health check status
docker inspect task-mgmt-user-service | grep Health -A 10
```

**Database Access:**

```bash
# PostgreSQL (development only)
docker exec -it task-mgmt-user-db psql -U user -d userdb_dev

# MongoDB (development only)
docker exec -it task-mgmt-task-db mongosh taskdb_dev
```

## Contributing

1. Follow the existing code structure and patterns
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure all services pass health checks
5. Test the complete system with Docker Compose
6. Test both development and production configurations
