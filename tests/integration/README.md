# Integration Tests

This directory contains comprehensive integration tests for the microservices task management system. These tests verify that all services work together correctly and that data flows properly across service boundaries.

## Test Structure

### Test Files

1. **`test_database_integration.py`** - Tests database consistency and integrity across all services
2. **`test_end_to_end_auth_flow.py`** - Tests complete authentication flow from registration to task management
3. **`test_service_interactions.py`** - Tests service-to-service communication and interactions
4. **`conftest.py`** - Shared fixtures and configuration for all integration tests
5. **`run_integration_tests.py`** - Test runner script with service health checks

### Test Categories

#### Database Integration Tests

- User creation consistency across services
- Task creation and data integrity
- Notification creation and synchronization
- Cross-service data integrity validation
- Database transaction consistency
- Concurrent operation handling
- Database connection resilience

#### End-to-End Authentication Tests

- Complete user journey from registration to task management
- JWT token consistency across all services
- Service-to-service communication with authentication
- Token validation and security
- Cross-service authorization

#### Service Interaction Tests

- User service interactions (registration, profile updates)
- Task service interactions (creation, updates, assignments)
- Notification service interactions (creation, reading, bulk operations)
- Cross-service data flow validation
- Service resilience and error handling
- Performance under concurrent load

## Prerequisites

### Services Must Be Running

Before running integration tests, ensure all services are running:

```bash
# Start all services
docker-compose up -d

# Or start individual services
docker-compose up -d user-service task-service notification-service
```

### Required Ports

- User Service: `http://localhost:8001`
- Task Service: `http://localhost:8002`
- Notification Service: `http://localhost:8003`

### Dependencies

Install test dependencies:

```bash
pip install pytest pytest-asyncio httpx
```

## Running Tests

### Run All Integration Tests

```bash
# Using the test runner (recommended)
python tests/integration/run_integration_tests.py

# Using pytest directly
python -m pytest tests/integration/ -v --asyncio-mode=auto
```

### Run Specific Test Suites

```bash
# Database integration tests
python tests/integration/run_integration_tests.py database

# Authentication flow tests
python tests/integration/run_integration_tests.py auth

# Service interaction tests
python tests/integration/run_integration_tests.py interactions
```

### Run Individual Test Files

```bash
# Database tests
python -m pytest tests/integration/test_database_integration.py -v --asyncio-mode=auto

# Auth flow tests
python -m pytest tests/integration/test_end_to_end_auth_flow.py -v --asyncio-mode=auto

# Service interaction tests
python -m pytest tests/integration/test_service_interactions.py -v --asyncio-mode=auto
```

### Run Specific Test Methods

```bash
# Run a specific test method
python -m pytest tests/integration/test_service_interactions.py::TestTaskServiceInteractions::test_task_creation_triggers_notification -v --asyncio-mode=auto
```

## Test Configuration

### Environment Variables

You can configure test behavior using environment variables:

```bash
# Service URLs (if different from defaults)
export USER_SERVICE_URL=http://localhost:8001
export TASK_SERVICE_URL=http://localhost:8002
export NOTIFICATION_SERVICE_URL=http://localhost:8003

# Test timeouts
export TEST_TIMEOUT=30
```

### Pytest Markers

Tests are marked with the following markers:

- `@pytest.mark.integration` - All integration tests
- `@pytest.mark.slow` - Tests that may take longer to run

Run only fast tests:

```bash
python -m pytest tests/integration/ -m "not slow" -v --asyncio-mode=auto
```

## Test Data Management

### Test Users

Tests automatically create and clean up test users with unique identifiers to avoid conflicts.

### Test Isolation

Each test runs in isolation with its own test data. Tests do not interfere with each other.

### Database State

Tests verify database state but do not modify production data. All test data uses unique identifiers.

## Troubleshooting

### Common Issues

#### Services Not Running

```
Error: Service is not accessible
```

**Solution**: Start all services with `docker-compose up -d`

#### Port Conflicts

```
Error: Connection refused
```

**Solution**: Check that services are running on expected ports (8001, 8002, 8003)

#### Database Connection Issues

```
Error: Database not found
```

**Solution**: Ensure databases are initialized. Run `docker-compose up -d` to create databases.

#### Authentication Failures

```
Error: 401 Unauthorized
```

**Solution**: Check that JWT tokens are being generated correctly. Verify user service is running.

### Debug Mode

Run tests with additional debugging:

```bash
# Enable debug logging
python -m pytest tests/integration/ -v -s --log-cli-level=DEBUG --asyncio-mode=auto

# Run with pdb on failure
python -m pytest tests/integration/ -v --pdb --asyncio-mode=auto
```

### Health Checks

The test runner includes health checks for all services:

```bash
# Check service health only
python tests/integration/run_integration_tests.py --health-check-only
```

## Test Coverage

### What Is Tested

- ✅ User registration and authentication
- ✅ Task creation, updates, and deletion
- ✅ Notification creation and management
- ✅ Cross-service data consistency
- ✅ JWT token validation across services
- ✅ Service-to-service communication
- ✅ Database transaction integrity
- ✅ Concurrent operation handling
- ✅ Error handling and resilience

### What Is Not Tested

- ❌ UI/Frontend interactions (covered by frontend tests)
- ❌ Performance benchmarking (separate performance tests)
- ❌ Load testing (separate load tests)
- ❌ Security penetration testing (separate security tests)

## Contributing

### Adding New Tests

1. Create test methods in appropriate test class
2. Use existing fixtures from `conftest.py`
3. Follow naming convention: `test_<functionality>_<expected_behavior>`
4. Add appropriate markers (`@pytest.mark.asyncio`, etc.)
5. Include proper assertions and error messages

### Test Guidelines

- Tests should be independent and not rely on other tests
- Use descriptive test names that explain what is being tested
- Include both positive and negative test cases
- Test error conditions and edge cases
- Use appropriate timeouts for async operations
- Clean up test data when necessary

### Example Test Structure

```python
@pytest.mark.asyncio
async def test_service_interaction_behavior(self, service_helper, test_users):
    """Test that service interaction behaves correctly."""
    # Arrange
    user = test_users[0]
    headers = {"Authorization": f"Bearer {user['token']}"}

    # Act
    response = await service_helper.make_request(
        "POST",
        f"{SERVICE_URL}/endpoint",
        headers=headers,
        json_data={"key": "value"}
    )

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["key"] == "expected_value"

    logger.info("✓ Service interaction test completed")
```

## Continuous Integration

These integration tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Integration Tests
  run: |
    docker-compose up -d
    sleep 10  # Wait for services to start
    python tests/integration/run_integration_tests.py
    docker-compose down
```

## Monitoring and Reporting

The test runner provides detailed reporting:

- Service health status
- Test execution time
- Pass/fail status for each test suite
- Detailed error messages for failures
- Summary of all test results

For CI/CD integration, the runner exits with appropriate status codes:

- `0` - All tests passed
- `1` - Some tests failed or services unavailable
