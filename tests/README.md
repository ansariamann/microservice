# Test Automation and CI/CD Pipeline

This directory contains the comprehensive test automation setup for the Microservices Task Management System. The testing infrastructure includes unit tests, integration tests, coverage reporting, and CI/CD pipeline configuration.

## 📁 Directory Structure

```
tests/
├── integration/           # Integration tests
│   ├── conftest.py       # Integration test fixtures
│   ├── test_*.py         # Integration test files
│   └── README.md         # Integration test documentation
├── README.md             # This file
└── test-config.yml       # Global test configuration

scripts/
├── run-tests.sh          # Comprehensive test runner (Unix)
├── run-tests.ps1         # Comprehensive test runner (Windows)
├── test-quick.sh         # Quick test runner for development
└── generate-coverage-report.py  # Coverage report generator

shared/
├── test_factories.py     # Test data factories
└── test_cleanup.py       # Test cleanup utilities

.github/workflows/
└── ci.yml               # GitHub Actions CI/CD pipeline
```

## 🚀 Quick Start

### Running Tests Locally

#### All Tests

```bash
# Unix/Linux/macOS
./scripts/run-tests.sh

# Windows PowerShell
.\scripts\run-tests.ps1
```

#### Specific Service Tests

```bash
# Unix/Linux/macOS
./scripts/test-quick.sh user --coverage
./scripts/test-quick.sh task --watch
./scripts/test-quick.sh frontend --verbose

# Windows PowerShell
.\scripts\run-tests.ps1 -Target user
.\scripts\run-tests.ps1 -Target frontend
```

#### Integration Tests Only

```bash
# Unix/Linux/macOS
./scripts/run-tests.sh integration

# Windows PowerShell
.\scripts\run-tests.ps1 -Target integration
```

### Docker-based Testing

```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
cd tests/integration
python -m pytest . -v

# Clean up
docker-compose -f docker-compose.test.yml down -v
```

## 🧪 Test Types

### Unit Tests

Each service has comprehensive unit tests covering:

- **User Service**: Authentication, user management, database operations
- **Task Service**: CRUD operations, authorization, MongoDB integration
- **Notification Service**: Notification creation, retrieval, SQLite operations
- **Frontend**: Component testing, API integration, user interactions

**Location**: `{service}/tests/`
**Command**: `pytest tests/` (for Python services), `npm test` (for frontend)

### Integration Tests

End-to-end tests that verify service interactions:

- User registration and authentication flow
- Task creation and assignment workflow
- Notification delivery across services
- Database integration and data consistency

**Location**: `tests/integration/`
**Command**: `python -m pytest tests/integration/`

### Coverage Testing

Comprehensive coverage reporting with configurable thresholds:

- **Global Threshold**: 80% line coverage
- **Service-specific Thresholds**: Defined in `test-config.yml`
- **Multiple Formats**: HTML, XML, JSON, LCOV

## 📊 Coverage Reporting

### Generate Combined Coverage Report

```bash
python scripts/generate-coverage-report.py
```

This generates:

- `coverage-reports/combined-coverage-report.html` - Interactive HTML report
- `coverage-reports/combined-coverage-report.json` - Machine-readable JSON report

### Coverage Thresholds

| Service              | Line Coverage | Branch Coverage |
| -------------------- | ------------- | --------------- |
| User Service         | 85%           | 80%             |
| Task Service         | 80%           | 75%             |
| Notification Service | 80%           | 75%             |
| Frontend             | 75%           | 70%             |
| **Overall**          | **80%**       | **75%**         |

## 🔧 Configuration

### Test Configuration File

The `test-config.yml` file contains all test settings:

```yaml
global:
  coverage_threshold: 80
  test_timeout: 300
  parallel_workers: 4

services:
  user-service:
    coverage_threshold: 85
    database:
      test_url: postgresql://testuser:testpass@localhost:5433/test_userdb
```

### Environment Variables

Each service can be configured with environment variables:

```bash
# User Service
export DATABASE_URL="postgresql://testuser:testpass@localhost:5433/test_userdb"
export JWT_SECRET="test-jwt-secret-key"

# Task Service
export MONGODB_URL="mongodb://localhost:27018/test_taskdb"
export NOTIFICATION_SERVICE_URL="http://localhost:8003"

# Notification Service
export DATABASE_URL="sqlite:///test_notifications.db"
```

## 🏗️ CI/CD Pipeline

### GitHub Actions Workflow

The CI/CD pipeline (`.github/workflows/ci.yml`) includes:

1. **Unit Tests** - Parallel execution for all services
2. **Integration Tests** - End-to-end service interaction testing
3. **Coverage Reporting** - Combined coverage analysis
4. **Docker Build** - Container image validation
5. **Artifact Upload** - Test results and coverage reports

### Pipeline Stages

```mermaid
graph TD
    A[Code Push/PR] --> B[Unit Tests]
    B --> C[Integration Tests]
    B --> D[Coverage Report]
    C --> E[Docker Build]
    D --> F[Coverage Analysis]
    E --> G[Deployment Ready]
```

### Triggers

- **Push** to `main` or `develop` branches
- **Pull Request** to `main` or `develop` branches

## 🛠️ Test Data Management

### Test Factories

The `shared/test_factories.py` module provides factories for creating consistent test data:

```python
from shared.test_factories import UserFactory, TaskFactory, NotificationFactory

# Create test user
user = UserFactory.create_user(email="test@example.com")

# Create test task
task = TaskFactory.create_task(title="Test Task", creator_id=user.id)

# Create test notification
notification = NotificationFactory.create_notification(
    user_id=user.id,
    task_id=task.id
)
```

### Test Cleanup

The `shared/test_cleanup.py` module provides utilities for cleaning up test data:

```python
from shared.test_cleanup import test_environment, get_test_config

# Use context manager for automatic cleanup
async with test_environment(get_test_config()) as (manager, temp_manager):
    # Run tests
    pass
# Cleanup happens automatically
```

## 📈 Performance and Monitoring

### Test Performance Metrics

- **Unit Test Execution Time**: < 2 minutes per service
- **Integration Test Execution Time**: < 5 minutes
- **Full Pipeline Execution Time**: < 15 minutes

### Monitoring and Alerts

- **Coverage Threshold Violations**: Pipeline fails if coverage drops below threshold
- **Test Failures**: Immediate notification via GitHub Actions
- **Performance Regression**: Tracked via test execution time metrics

## 🔍 Debugging Tests

### Local Debugging

```bash
# Run tests with verbose output
./scripts/test-quick.sh user --verbose

# Run specific test file
cd user-service
pytest tests/test_auth.py -v -s

# Run tests with debugger
pytest tests/test_auth.py --pdb
```

### Docker Debugging

```bash
# Check service logs
docker-compose -f docker-compose.test.yml logs user-service

# Execute commands in running container
docker-compose -f docker-compose.test.yml exec user-service bash

# Debug integration test environment
docker-compose -f docker-compose.test.yml ps
```

## 📝 Writing New Tests

### Unit Test Example

```python
# user-service/tests/test_new_feature.py
import pytest
from shared.test_factories import UserFactory

def test_new_user_feature(db_session):
    # Arrange
    user = UserFactory.create_user()

    # Act
    result = new_user_feature(user)

    # Assert
    assert result.success is True
    assert result.data is not None
```

### Integration Test Example

```python
# tests/integration/test_new_workflow.py
import pytest
from tests.integration.conftest import assert_valid_response

async def test_new_workflow(http_client, clean_test_user):
    # Test new workflow end-to-end
    response = await http_client.post("/api/v1/new-endpoint", json={...})
    assert_valid_response(response, 201)
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Errors**

   ```bash
   # Check if test databases are running
   docker-compose -f docker-compose.test.yml ps
   ```

2. **Coverage Threshold Failures**

   ```bash
   # Generate detailed coverage report
   python scripts/generate-coverage-report.py --threshold 70
   ```

3. **Integration Test Timeouts**
   ```bash
   # Increase service startup wait time
   export INTEGRATION_SETUP_TIMEOUT=120
   ```

### Getting Help

- Check service logs: `docker-compose -f docker-compose.test.yml logs [service]`
- Review test configuration: `test-config.yml`
- Examine coverage reports: `coverage-reports/combined-coverage-report.html`
- Check CI/CD pipeline: GitHub Actions tab in repository

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Docker Compose Testing](https://docs.docker.com/compose/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

For questions or issues with the testing setup, please create an issue in the repository or contact the development team.
