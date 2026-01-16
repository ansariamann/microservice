# Development Environment Setup Guide

This guide provides detailed instructions for setting up the Task Management System for development.

## Prerequisites

### Required Software

- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **Git** for version control
- **Code Editor** (VS Code recommended with extensions)

### Optional for Local Development

- **Python 3.11+** for running services locally
- **Node.js 18+** for frontend development
- **PostgreSQL Client** for database debugging
- **MongoDB Compass** for MongoDB debugging

### System Requirements

- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB free space
- **OS**: Linux, macOS, or Windows with WSL2

## Initial Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd microservices-task-management
```

### 2. Run Setup Script

The setup script creates environment files and makes scripts executable:

```bash
./scripts/manage.sh setup
```

This creates:

- `.env` - Development environment variables
- `.env.prod` - Production environment template

### 3. Configure Environment Variables

Edit the `.env` file to customize your development environment:

```bash
nano .env
```

**Key Configuration Options:**

```bash
# Security - Change this for production
JWT_SECRET=your-development-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Database Configuration
POSTGRES_DB=userdb_dev
POSTGRES_USER=user
POSTGRES_PASSWORD=devpassword
POSTGRES_PORT=5432

MONGODB_DATABASE=taskdb_dev
MONGODB_PORT=27017

# Service Ports
USER_SERVICE_PORT=8001
TASK_SERVICE_PORT=8002
NOTIFICATION_SERVICE_PORT=8003
FRONTEND_PORT=3000

# Development Settings
DEBUG=true
LOG_LEVEL=DEBUG
LOG_FORMAT=pretty

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Frontend Configuration
REACT_APP_API_BASE_URL=http://localhost:8080
REACT_APP_USER_SERVICE_URL=http://localhost:8001
REACT_APP_TASK_SERVICE_URL=http://localhost:8002
REACT_APP_NOTIFICATION_SERVICE_URL=http://localhost:8003
```

## Development Workflows

### Option 1: Full Docker Development (Recommended)

Start all services with Docker Compose:

```bash
# Start all services
./scripts/manage.sh dev

# Start with monitoring stack
./scripts/manage.sh dev --monitoring

# Start in background
./scripts/manage.sh dev --detached
```

**Advantages:**

- Consistent environment across team members
- No need to install language runtimes locally
- Includes databases and all dependencies
- Easy to reset and clean up

**Development Features:**

- Hot reload for all services
- Source code mounted as volumes
- Exposed database ports for debugging
- Debug logging enabled

### Option 2: Hybrid Development

Run databases in Docker, services locally:

```bash
# Start only databases
docker-compose up -d user-db task-db

# Run services locally (in separate terminals)
cd user-service && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8001
cd task-service && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8002
cd notification-service && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8003
cd frontend && npm install && npm run dev
```

**Advantages:**

- Faster service restarts
- Direct debugging capabilities
- IDE integration works better
- Can use local Python/Node versions

### Option 3: Individual Service Development

Focus on one service at a time:

```bash
# Start dependencies for user service
docker-compose up -d user-db

# Run user service locally
cd user-service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

## Development Tools and Commands

### Management Script

The `./scripts/manage.sh` script provides convenient commands:

```bash
# Environment management
./scripts/manage.sh dev                    # Start development environment
./scripts/manage.sh dev --monitoring       # Start with monitoring
./scripts/manage.sh dev --detached        # Start in background
./scripts/manage.sh stop dev              # Stop development environment

# Monitoring and debugging
./scripts/manage.sh status                 # Show container status
./scripts/manage.sh health                 # Check service health
./scripts/manage.sh logs                   # View all logs
./scripts/manage.sh logs user-service      # View specific service logs

# Cleanup
./scripts/manage.sh clean                  # Remove all containers and volumes
```

### Testing Commands

```bash
# Run all tests
./scripts/run-tests.sh

# Run specific service tests
cd user-service && python -m pytest
cd task-service && python -m pytest -v
cd notification-service && python -m pytest --cov=app
cd frontend && npm test

# Run integration tests
cd tests/integration && python -m pytest
```

### Database Access

**PostgreSQL (User Service):**

```bash
# Connect to database
docker exec -it task-mgmt-user-db psql -U user -d userdb_dev

# Common queries
\dt                           # List tables
SELECT * FROM users;          # View users
\q                           # Quit
```

**MongoDB (Task Service):**

```bash
# Connect to database
docker exec -it task-mgmt-task-db mongosh taskdb_dev

# Common queries
show collections              # List collections
db.tasks.find().pretty()     # View tasks
exit                         # Quit
```

**SQLite (Notification Service):**

```bash
# Connect to database
docker exec -it task-mgmt-notification-service sqlite3 /app/notifications.db

# Common queries
.tables                      # List tables
SELECT * FROM notifications; # View notifications
.quit                       # Quit
```

## IDE Configuration

### VS Code Setup

Recommended extensions:

- Python
- Docker
- REST Client
- Thunder Client
- GitLens
- Prettier
- ESLint

**Workspace Settings (.vscode/settings.json):**

```json
{
  "python.defaultInterpreterPath": "./user-service/venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "typescript.preferences.importModuleSpecifier": "relative",
  "editor.formatOnSave": true,
  "docker.showStartPage": false
}
```

**Launch Configuration (.vscode/launch.json):**

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug User Service",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/user-service/app/main.py",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}/user-service",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "Debug Task Service",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/task-service/app/main.py",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}/task-service"
    }
  ]
}
```

### PyCharm Setup

1. Open project root directory
2. Configure Python interpreters for each service
3. Set up run configurations for each service
4. Configure test runners for pytest

## Development Best Practices

### Code Style

**Python Services:**

- Follow PEP 8 style guide
- Use type hints
- Write docstrings for functions and classes
- Use Black for code formatting
- Use flake8 for linting

**Frontend:**

- Use TypeScript for type safety
- Follow React best practices
- Use Prettier for code formatting
- Use ESLint for linting

### Testing

**Backend Testing:**

- Write unit tests for business logic
- Write integration tests for API endpoints
- Use pytest fixtures for test data
- Mock external dependencies
- Aim for >80% code coverage

**Frontend Testing:**

- Write unit tests for components
- Write integration tests for user flows
- Use React Testing Library
- Mock API calls
- Test error scenarios

### Git Workflow

1. Create feature branches from `main`
2. Make small, focused commits
3. Write descriptive commit messages
4. Run tests before committing
5. Create pull requests for code review
6. Squash commits when merging

### Environment Management

- Never commit `.env` files
- Use `.env.template` for documentation
- Keep development and production configs separate
- Use strong secrets in production
- Document environment variable changes

## Troubleshooting

### Common Issues

**Port Conflicts:**

```bash
# Check what's using a port
lsof -i :8001

# Kill process using port
kill -9 $(lsof -t -i:8001)
```

**Docker Issues:**

```bash
# Clean up Docker resources
docker system prune -a

# Rebuild containers
docker-compose build --no-cache

# Reset volumes
docker-compose down -v
```

**Database Connection Issues:**

```bash
# Check database container logs
docker logs task-mgmt-user-db

# Restart database container
docker-compose restart user-db
```

**Service Health Issues:**

```bash
# Check service health
./scripts/manage.sh health

# View service logs
./scripts/manage.sh logs user-service

# Check container status
docker-compose ps
```

### Performance Issues

**Slow Container Startup:**

- Increase Docker memory allocation
- Use `.dockerignore` files
- Optimize Dockerfile layers

**High Memory Usage:**

- Monitor with `docker stats`
- Adjust container memory limits
- Check for memory leaks in application code

### Debugging Tips

**Backend Services:**

- Use `print()` statements for quick debugging
- Use Python debugger (`pdb`) for complex issues
- Check service logs for error messages
- Use health check endpoints to verify service status

**Frontend:**

- Use browser developer tools
- Check network tab for API call issues
- Use React Developer Tools extension
- Check console for JavaScript errors

**Database Issues:**

- Check database logs
- Verify connection strings
- Test database connectivity
- Check for schema migration issues

## Next Steps

After setting up your development environment:

1. **Explore the API Documentation**: Visit the Swagger UI for each service
2. **Run the Test Suite**: Ensure all tests pass
3. **Make a Small Change**: Try modifying a service and see the hot reload
4. **Check Monitoring**: Start with `--monitoring` to see metrics
5. **Read the Code**: Understand the service architecture and patterns

For production deployment, see [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md).
